"""distutils extension module - create an installer by InnoSetup.

Requirements
------------

* Python 2.5 or later

* `py2exe <http://pypi.python.org/pypi/py2exe>`_

* `pywin32 <http://pypi.python.org/pypi/pywin32>`_

* `InnoSetup <http://www.innosetup.com/>`_


Features
--------

* You can use your customized InnoSetup Script.

* installer metadata over setup() metadata

* generate AppId(GUID) from setup() metadata
  See the innosetup.InnoScript.appid property.

* bundle exe and com dll and dependent libs and resources

* bundle msvcr and mfc and their manifest

* bundle all installed InnoSetup's language file
  (If there is no valid [Languages] section.)

* create `windows` exe's shortcut

* register `com_server` and `service`

* check the Windows version with Python version

* fix a problem py2exe.mf misses some modules (ex. win32com.shell)


An example
----------
::

    from distutils.core import setup
    import py2exe, innosetup

    # All options are same as py2exe options.
    setup(
        name='example',
        version='1.0.0.0',
        license='PSF or other',
        author='you',
        author_email='you@your.domain',
        description='description',
        url='http://www.your.domain/example', # generate AppId from this url
        options={
            'py2exe': {
                # `innosetup` gets the `py2exe`'s options.
                'compressed': True,
                'optimize': 2,
                'bundle_files': 3,
                },
            'innosetup': {
                # user defined iss file path or iss string
                'inno_script': innosetup.DEFAULT_ISS, # default is ''
                # bundle msvc files
                'bundle_vcr': True, # default is True
                # zip setup file
                'zip': False, # default is False, bool() or zip file name
                # create shortcut to startup if you want. 
                'regist_startup': True, # default is False
                }
            },
        com_server=[
            {'modules': ['your_com_server_module'], 'create_exe': False},
            ],
        # and other metadata ...
        )

Do the command `setup.py innosetup`.
Then you get InnoSetup script file named `dist\distutils.iss` and
the installation file named `dist\example-1.0.0.0.exe`.


History
-------

0.6.3
-----

* change versioning policy (remove build number).

* add utf-8 bom to .iss file by Jerome Ortais, thanx.

* pick up `COPYING` file for `[setup]/LicenseFile` by Jerome Ortais, thanx.

0.6.0.2
~~~~~~~

* add `regist_startup` option for create shortcut to startup.

0.6.0.1
~~~~~~~

* fix metadata and unicode by surgo, thanx.

* set `DEFAULT_ISS` to empty because `Inno Setup 5.3.9` is released.

* fix a problem that `py2exe` includes MinWin's ApiSet Stub DLLs on Windows 7.

0.6.0.0
~~~~~~~

* support bundling tcl files

* change OutputBaseFilename

0.5.0.1
~~~~~~~

* improve update install support

0.5.0.0
~~~~~~~

* add DEFAULT_ISS, manifest, srcname, srcnames

* add `zip` option

* fix `bundle_files=1` option problem (always bundle pythonXX.dll)

* add `DefaultGroupName`, `InfoBeforeFile`, `LicenseFile` into `[Setup]`
  section

0.4.0.0
~~~~~~~

* support service cmdline_style options

* rewrite codes around iss file

0.3.0.0
~~~~~~~

* improve the InnoSetup instllation path detection

* add `inno_setup_exe` option

0.2.0.0
~~~~~~~

* handle `py2exe`'s command options

* add `bundle_vcr` option

0.1.0.0
~~~~~~~

* first release


"""
import sys, imp, os, platform, subprocess, codecs, ctypes, uuid, _winreg, \
       distutils.msvccompiler
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree
import win32api # for read pe32 resource
from py2exe.build_exe import *
from py2exe import build_exe, mf as modulefinder


DEFAULT_ISS = ""
DEFAULT_CODES = """
procedure ExecIfExists(const FileName, Arg: String);
var
    ret: Integer;
begin
    FileName := ExpandConstant(FileName);
    if FileExists(FileName) then begin
        if not Exec(FileName, Arg, '', SW_HIDE, ewWaitUntilTerminated, ret) then
            RaiseException('error: ' + FileName + ' ' + Arg);
    end;
end;
procedure UnregisterPywin32Service(const FileName: String);
begin
    try
        ExecIfExists(FileName, 'stop');
    except
        //already stopped or stop error
    end;
    ExecIfExists(FileName, 'remove');
end;
procedure UnregisterServerIfExists(const FileName: String);
begin
    FileName := ExpandConstant(FileName);
    if FileExists(FileName) then begin
        if not UnregisterServer(%(x64)s, FileName, False) then
            RaiseException('error: unregister ' + FileName);
    end;
end;
""" % {'x64': platform.machine() == 'AMD64', }


def manifest(name, res_id=1):
    data = manifest.template % name
    return RT_MANIFEST, res_id, data


manifest.template = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
<assemblyIdentity
    type="win32"
    name="Controls"
    version="5.0.0.0"
    processorArchitecture="x86"
    />
<description>%s</description>
<dependency>
    <dependentAssembly>
        <assemblyIdentity
            type="win32"
            name="Microsoft.Windows.Common-Controls"
            version="6.0.0.0"
            processorArchitecture="X86"
            publicKeyToken="6595b64144ccf1df"
            language="*"
            />
    </dependentAssembly>
</dependency>
</assembly>"""


def load_manifest(handle):
    """get the first manifest string from HMODULE"""
    for restype in (RT_MANIFEST, ): #win32api.EnumResourceTypes(handle)
        for name in win32api.EnumResourceNames(handle, restype):
            return win32api.LoadResource(handle, restype, name).decode('utf_8')


def srcname(dottedname):
    """get the source filename from importable name or module"""
    if hasattr(dottedname, '__file__'):
        module = dottedname
    else:
        names = dottedname.split('.')
        module = __import__(names.pop(0))
        for name in names:
            module = getattr(module, name)

    filename = module.__file__
    name, ext = os.path.splitext(filename)
    ext = ext.lower()

    _py_src_suffixes = [i[0] for i in imp.get_suffixes()
                             if i[2] == imp.PY_SOURCE]

    if ext not in build_exe._py_suffixes:
        raise ValueError('not python script')

    if ext in _py_src_suffixes:
        return filename

    for i in _py_src_suffixes:
        if os.path.isfile(name + i):
            return name + i

    raise ValueError('not found')


def srcnames(*args):
    """get the source filename from importable name or module"""
    return [srcname(i) for i in args]


def modname(handle):
    """get module filename from HMODULE"""
    b = ctypes.create_unicode_buffer('', 1024)
    ctypes.windll.kernel32.GetModuleFileNameW(handle, b, 1024)
    return b.value


def findfiles(filenames, *conditions):
    """filter `filenames` by conditions"""
    def check(filename):
        filename = filename.lower()
        for i in conditions:
            i = i.lower()
            if i.startswith('.'): #compare ext
                if os.path.splitext(filename)[1] != i:
                    return
            elif i.count('.') == 1: #compare basename
                if os.path.basename(filename) != i:
                    return
            else: # contains
                if i not in os.path.basename(filename):
                    return
        return True

    return [i for i in filenames if check(i)]


hkshortnames = {
    'HKLM': _winreg.HKEY_LOCAL_MACHINE,
    'HKCU': _winreg.HKEY_CURRENT_USER,
    'HKCR': _winreg.HKEY_CLASSES_ROOT,
    'HKU': _winreg.HKEY_USERS,
    'HKCC': _winreg.HKEY_CURRENT_CONFIG,
    'HKDD': _winreg.HKEY_DYN_DATA,
    'HKPD': _winreg.HKEY_PERFORMANCE_DATA,
    }


def getregvalue(path, default=None):
    """get registry value

    noname value
    >>> getregvalue('HKEY_CLASSES_ROOT\\.py\\')
    'Python.File'

    named value
    >>> getregvalue('HKEY_CLASSES_ROOT\\.py\\Content Type')
    ''text/plain
    """
    root, subkey = path.split('\\', 1)
    if root.startswith('HKEY_'):
        root = getattr(_winreg, root)
    elif root in hkshortnames:
        root = hkshortnames[root]
    else:
        root = _winreg.HKEY_CURRENT_USER
        subkey = path

    subkey, name = subkey.rsplit('\\', 1)

    try:
        handle = _winreg.OpenKey(root, subkey)
        value, typeid = _winreg.QueryValueEx(handle, name)
        return value
    except EnvironmentError:
        return default


class IssFile(file):
    """file object with useful method `issline`"""
    noescape = ['Flags', ]

    def issline(self, **kwargs):
        args = []
        for k, v in kwargs.items():
            if k not in self.noescape:
                # ' -> ''
                v = '"%s"' % v
            args.append('%s: %s' % (k, v, ))
        self.write('; '.join(args) + '\n')


class InnoScript(object):

    consts_map = dict(
        AppName='%(name)s',
        AppVerName='%(name)s %(version)s',
        AppVersion='%(version)s',
        VersionInfoVersion='%(version)s',
        AppCopyright='%(author)s',
        AppContact='%(author_email)s',
        AppComments='%(description)s',
        AppPublisher='%(author)s',
        AppPublisherURL='%(url)s',
        AppSupportURL='%(url)s',
        )
    metadata_map = dict(
        SolidCompression='yes',
        DefaultGroupName='%(name)s',
        DefaultDirName='{pf}\\%(name)s',
        OutputBaseFilename='%(name)s-%(version)s-setup',
        )
    metadata_map.update(consts_map)
    required_sections = (
        'Setup', 'Files', 'Run', 'UninstallRun', 'Languages', 'Icons', 'Code',
        )
    default_flags = (
        'ignoreversion', 'overwritereadonly', 'uninsremovereadonly',
        )
    default_dir_flags = (
        'recursesubdirs', 'createallsubdirs',
        )
    bin_exts = ('.exe', '.dll', '.pyd', )
    iss_metadata = {}

    def __init__(self, builder):
        self.builder = builder
        self.issfile = os.path.join(self.builder.dist_dir, 'distutils.iss')

    def parse_iss(self, s):
        firstline = ''
        sectionname = ''
        lines = []
        for line in s.splitlines():
            if line.startswith('[') and ']' in line:
                if lines: yield firstline, sectionname, lines
                firstline = line
                sectionname = line[1:line.index(']')].strip()
                lines = []
            else:
                lines.append(line)
        if lines: yield firstline, sectionname, lines

    def chop(self, filename, dirname=''):
        """get relative path"""
        if not dirname:
            dirname = self.builder.dist_dir
        if not dirname[-1] in "\\/":
            dirname += "\\"
        if filename.startswith(dirname):
            filename = filename[len(dirname):]
        #else:
        #    filename = os.path.basename(filename)
        return filename

    @property
    def metadata(self):
        metadata = dict((k, v or '') for k, v in
                        self.builder.distribution.metadata.__dict__.items())
        return metadata

    @property
    def appid(self):
        m = self.metadata
        if m['url']:
            src = m['url']
        elif m['name'] and m['version'] and m['author_email']:
            src = 'mailto:%(author_email)s?subject=%(name)s-%(version).1s' % m
        elif m['name'] and m['author_email']:
            src = 'mailto:%(author_email)s?subject=%(name)s' % m
        else:
            return m['name']
        appid = uuid.uuid5(uuid.NAMESPACE_URL, src).urn.rsplit(':', 1)[1]
        return '{{%s}' % appid

    @property
    def iss_consts(self):
        metadata = self.metadata
        return dict((k, v % metadata) for k, v in self.consts_map.items())

    @property
    def innoexepath(self):
        if self.builder.inno_setup_exe:
            return self.builder.inno_setup_exe

        result = getregvalue(
            'HKCR\\InnoSetupScriptFile\\shell\\compile\\command\\')
        if result:
            if result.startswith('"'):
                result = result[1:].split('"', 1)[0]
            else:
                result = result.split()[0]
            return result

        result = getregvalue(
            'HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion'
            '\\Uninstall\\Inno Setup 5_is1\\InstallLocation')
        if result:
            return os.path.join(result, 'Compil32.exe')

        result = getregvalue(
            'HKLM\\SOFTWARE\\Wow6432Node\\Microsoft\\Windows'
            '\\CurrentVersion\\Uninstall\\Inno Setup 5_is1\\InstallLocation')
        if result:
            return os.path.join(result, 'Compil32.exe')

        return ''

    @property
    def msvcfiles(self):
        # msvcrXX
        vcver = '%.2d' % (distutils.msvccompiler.get_build_version() * 10, )
        assemblename = 'Microsoft.VC%s.CRT' % vcver
        msvcr = getattr(ctypes.windll, 'msvcr' + vcver)
        vcrname = modname(msvcr._handle)
        yield vcrname

        # bundled file
        manifestfile = os.path.join(os.path.dirname(vcrname),
                                    assemblename + '.manifest')
        if os.path.isfile(manifestfile):
            pass

        # SxS
        else:
            manifestfile = os.path.join(self.builder.dist_dir,
                                        assemblename + '.manifest')

            doc = ElementTree.fromstring(load_manifest(sys.dllhandle))
            for e in doc.getiterator('{urn:schemas-microsoft-com:asm.v1}'
                                     'assemblyIdentity'):
                if e.attrib['name'] == assemblename: break
            else:
                raise EnvironmentError('no msvcr manifets file found')

            dirname = os.path.join(os.path.dirname(os.path.dirname(vcrname)),
                                   'Manifests')
            src = os.path.join(dirname, findfiles(os.listdir(dirname),
                assemblename, e.attrib['version'],
                e.attrib['processorArchitecture'], '.manifest')[0])
            data = open(src, 'rb').read()
            open(manifestfile, 'wb').write(data)

        yield manifestfile

        # mfc files
        mfcfiles = findfiles(self.builder.other_depends, 'mfc%s.dll' % vcver)
        if mfcfiles:
            dirname = os.path.dirname(mfcfiles[0])
            for i in findfiles(os.listdir(dirname), 'mfc'):
                yield os.path.join(dirname, i)

    def handle_iss(self, lines, fp):
        for line in lines:
            fp.write(line + '\n')

    def handle_iss_setup(self, lines, fp):
        metadata = self.metadata
        iss_metadata = dict((k, v % metadata)
                            for k, v in self.metadata_map.items())
        iss_metadata['OutputDir'] = self.builder.dist_dir
        iss_metadata['AppId'] = self.appid

        if self.builder.service_exe_files or self.builder.comserver_files:
            iss_metadata['PrivilegesRequired'] = 'admin'

        # add InfoBeforeFile
        for filename in ('README', 'README.txt', ):
            if os.path.isfile(filename):
                iss_metadata['InfoBeforeFile'] = os.path.abspath(filename)
                break

        # add LicenseFile
        for filename in ('license.txt', 'COPYING', ):
            if os.path.isfile(filename):
                iss_metadata['LicenseFile'] = os.path.abspath(filename)
                break

        # Python 2.6 doesn't support Windows 9x and me.
        if sys.version_info > (2, 6):
            iss_metadata['MinVersion'] = '5.0,5.0'

        # handle user operations
        user = {}
        for line in lines:
            m = re.match('\s*(\w+)\s*=\s*(.*)\s*', line)
            if m:
                name, value = m.groups()
                if name in iss_metadata:
                    del iss_metadata[name]
                user[name] = value
                fp.write('%s=%s\n' % (name, value, ))
            else:
                fp.write(line + '\n')

        if 'AppId' in iss_metadata:
            print('There is no "AppId" in "[Setup]" section.\n'
            '"AppId" is automatically generated from metadata (%s),'
            'not a random value.' % iss_metadata['AppId'])

        for k in sorted(iss_metadata):
            fp.write(('%s=%s\n' % (k, iss_metadata[k], )).encode('utf_8'))


        self.iss_metadata = {}
        self.iss_metadata.update(iss_metadata)
        self.iss_metadata.update(user)

        fp.write('\n')

    def handle_iss_files(self, lines, fp):
        files = []
        excludes = []

        files.extend(self.builder.console_exe_files)
        files.extend(self.builder.windows_exe_files)
        files.extend(self.builder.service_exe_files)
        files.extend(self.builder.comserver_files)
        if self.builder.bundle_vcr:
            files.extend(self.msvcfiles)
        files.extend(self.builder.lib_files) #include data_files

        # problem with py2exe
        if self.builder.bundle_files < 2:
            excludes.extend(
                findfiles(files, os.path.basename(modname(sys.dllhandle))))

        # Python 2.6 or later doesn't support Windows 9x and me.
        if sys.version_info > (2, 6):
            excludes.extend(findfiles(files, 'w9xpopen.exe'))

        # handle Tkinter
        if 'Tkinter' in self.builder.modules:
            tcl_dst_dir = os.path.join(self.builder.lib_dir, 'tcl')
            files.append(tcl_dst_dir)

        stored = set()
        for filename in files:
            if filename in excludes: continue
            relname = self.chop(filename)
            # user operation given or already wrote
            if relname in ''.join(lines) or relname in stored: continue

            flags = list(self.default_flags)
            place = ''

            if os.path.isfile(filename):
                if os.path.splitext(relname)[1].lower() in self.bin_exts:
                    flags.append('restartreplace')
                    flags.append('uninsrestartdelete')

                if filename.startswith(self.builder.dist_dir):
                    place = os.path.dirname(relname)

                extraargs = {}
                if filename in self.builder.comserver_files:
                    if filename.lower().endswith('.exe'):
                        extraargs['BeforeInstall'] = \
                            "ExecIfExists('{app}\\%s', '/unregister')" \
                            % relname
                    else:
                        flags.append('regserver')
                        extraargs['BeforeInstall'] = \
                            "UnregisterServerIfExists('{app}\\%s')" % relname
                elif filename in self.builder.service_exe_files:
                    cmdline_style = \
                        self.builder.fileinfo[filename]['cmdline_style']
                    if cmdline_style == 'py2exe':
                        extraargs['BeforeInstall'] = \
                            "ExecIfExists('{app}\\%s', '-remove')" % relname
                    elif cmdline_style == 'pywin32':
                        extraargs['BeforeInstall'] = \
                            "UnregisterPywin32Service('{app}\\%s')" % relname

            else: # isdir
                if filename.startswith(self.builder.dist_dir):
                    place = relname
                relname += '\\*'
                flags.extend(self.default_dir_flags)

            fp.issline(
                Source=relname,
                DestDir="{app}\\%s" % place,
                Flags=' '.join(flags),
                **extraargs
                )
            stored.add(relname)

        self.handle_iss(lines, fp)

    def _iter_bin_files(self, attrname, lines=[]):
        for filename in getattr(self.builder, attrname, []):
            relname = self.chop(filename)
            if relname in ''.join(lines): continue
            yield filename, relname

    def handle_iss_run(self, lines, fp):
        self.handle_iss(lines, fp)

        for _, filename in self._iter_bin_files('comserver_files', lines):
            if filename.lower().endswith('.exe'):
                fp.issline(
                    Filename="{app}\\%s" % filename,
                    Parameters="/register",
                    WorkingDir="{app}",
                    Flags='runhidden',
                    StatusMsg="Registering %s..." % os.path.basename(filename),
                    )

        it = self._iter_bin_files('service_exe_files', lines)
        for orgname, filename in it:
            cmdline_style = self.builder.fileinfo[orgname]['cmdline_style']
            if cmdline_style == 'py2exe':
                fp.issline(
                    Filename="{app}\\%s" % filename,
                    Parameters="-install -auto",
                    WorkingDir="{app}",
                    Flags='runhidden',
                    StatusMsg="Registering %s..." % os.path.basename(filename),
                    )
            elif cmdline_style == 'pywin32':
                fp.issline(
                    Filename="{app}\\%s" % filename,
                    Parameters="--startup auto install",
                    WorkingDir="{app}",
                    Flags='runhidden',
                    StatusMsg="Registering %s..." % os.path.basename(filename),
                    )
                fp.issline(
                    Filename="{app}\\%s" % filename,
                    Parameters="start",
                    WorkingDir="{app}",
                    Flags='runhidden',
                    StatusMsg="Starting %s..." % os.path.basename(filename),
                    )

    def handle_iss_uninstallrun(self, lines, fp):
        self.handle_iss(lines, fp)

        for _, filename in self._iter_bin_files('comserver_files', lines):
            if filename.lower().endswith('.exe'):
                fp.issline(
                    Filename="{app}\\%s" % filename,
                    Parameters="/unregister",
                    WorkingDir="{app}",
                    Flags='runhidden',
                    StatusMsg=
                        "Unregistering %s..." % os.path.basename(filename),
                    )

        it = self._iter_bin_files('service_exe_files', lines)
        for orgname, filename in it:
            cmdline_style = self.builder.fileinfo[orgname]['cmdline_style']
            if cmdline_style == 'py2exe':
                fp.issline(
                    Filename="{app}\\%s" % filename,
                    Parameters="-remove",
                    WorkingDir="{app}",
                    Flags='runhidden',
                    StatusMsg=
                        "Unregistering %s..." % os.path.basename(filename),
                    )
            elif cmdline_style == 'pywin32':
                fp.issline(
                    Filename="{app}\\%s" % filename,
                    Parameters="stop",
                    WorkingDir="{app}",
                    Flags='runhidden',
                    StatusMsg=
                        "Stopping %s..." % os.path.basename(filename),
                    )
                fp.issline(
                    Filename="{app}\\%s" % filename,
                    Parameters="remove",
                    WorkingDir="{app}",
                    Flags='runhidden',
                    StatusMsg=
                        "Unregistering %s..." % os.path.basename(filename),
                    )

    def handle_iss_icons(self, lines, fp):
        self.handle_iss(lines, fp)
        for _, filename in self._iter_bin_files('windows_exe_files', lines):
            fp.issline(
                Name="{group}\\%s" % self.metadata['name'],
                Filename="{app}\\%s" % filename,
                )
        if self.builder.windows_exe_files:
            fp.issline(
                Name="{group}\\Uninstall %s" % self.metadata['name'],
                Filename="{uninstallexe}",
                )
            if self.builder.regist_startup:
                fp.issline(
                    Name="{commonstartup}\\%s" % self.metadata['name'],
                    Filename="{app}\\%s" % filename,
                    )

    def handle_iss_languages(self, lines, fp):
        self.handle_iss(lines, fp)

        if lines:
            return

        innopath = os.path.dirname(self.innoexepath)
        for root, dirs, files in os.walk(innopath):
            for basename in files:
                if not basename.lower().endswith('.isl'): continue
                filename = self.chop(os.path.join(root, basename), innopath)
                fp.issline(
                    Name=os.path.splitext(basename)[0],
                    MessagesFile="compiler:%s" % filename,
                    )

    def handle_iss_code(self, lines, fp):
        self.handle_iss(lines, fp)
        fp.write(DEFAULT_CODES)

    def create(self):

        inno_script = os.path.join(os.path.dirname(self.builder.dist_dir),
                                   self.builder.inno_script)
        if os.path.isfile(inno_script):
            inno_script = open(inno_script).read()
        else:
            inno_script = self.builder.inno_script

        fp = IssFile(self.issfile, 'w')
        fp.write(codecs.BOM_UTF8)
        fp.write('; This file is created by distutils InnoSetup extension.\n')

        # write "#define CONSTANT value"
        consts = self.iss_consts
        consts.update({
            'PYTHON_VERION': '%d.%d' % sys.version_info[:2],
            'PYTHON_VER': '%d%d' % sys.version_info[:2],
            'PYTHON_DIR': sys.prefix,
            'PYTHON_DLL': modname(sys.dllhandle),
            })
        consts.update((k.upper(), v) for k, v in self.metadata.items())
        for k in sorted(consts):
            fp.write(('#define %s "%s"\n' % (k, consts[k], )).encode('utf_8'))

        fp.write('\n')

        # handle sections
        sections = set()
        for firstline, name, lines in self.parse_iss(inno_script):
            if firstline:
                fp.write(firstline + '\n')
            handler = getattr(self, 'handle_iss_%s' % name.lower(),
                              self.handle_iss)
            handler(lines, fp)
            fp.write('\n')
            sections.add(name)

        for name in self.required_sections:
            if name not in sections:
                fp.write('[%s]\n' % name)
                handler = getattr(self, 'handle_iss_%s' % name.lower())
                handler([], fp)
                fp.write('\n')

    def compile(self):
        subprocess.call([self.innoexepath, '/cc', self.issfile])

        outputdir = self.iss_metadata.get('OutputDir',
            os.path.join(os.path.dirname(self.issfile), 'Output'))
        setupfile = os.path.join(outputdir,
            self.iss_metadata.get('OutputBaseFilename', 'setup') + '.exe')

        # zip the setup file
        if self.builder.zip:
            if isinstance(self.builder.zip, basestring):
                zipname = self.builder.zip
            else:
                zipname = setupfile + '.zip'

            zip = ZipFile(zipname, 'w', ZIP_DEFLATED)
            zip.write(setupfile, os.path.basename(setupfile))
            zip.close()

            self.builder.distribution.dist_files.append(
                ('innosetup', '', zipname))
        else:
            self.builder.distribution.dist_files.append(
                ('innosetup', '', setupfile))


class innosetup(py2exe):

    # setup()'s argument is in self.distribution.
    user_options = py2exe.user_options + [
        ('inno-setup-exe=', None,
         'a path to InnoSetup exe file (Compil32.exe)'),
        ('inno-script=', None,
         'a path to InnoSetup script file or an InnoSetup script string'),
        ('bundle-vcr=', None,
         'bundle msvc*XX.dll and mfc*.dll and their manifest files'),
         ('zip=', None, 'zip setup file'),
        ]
    description = 'create an executable file and an installer by InnoSetup'
    fileinfo = {}
    modules = {}

    def initialize_options(self):
        # get py2exe's command options
        options = dict(self.distribution.command_options.get('py2exe', {}))
        options.update(self.distribution.command_options.get('innosetup', {}))
        self.distribution.command_options['innosetup'] = options

        py2exe.initialize_options(self)
        self.inno_setup_exe = ''
        self.inno_script = ''
        self.bundle_vcr = True
        self.zip = False
        self.regist_startup = False
        self.fileinfo = {}
        self.modules = {}

    def build_service(self, target, template, arcname):
        result = py2exe.build_service(self, target, template, arcname)
        self.fileinfo.setdefault(result, {})['cmdline_style'] = \
            getattr(target, "cmdline_style", "py2exe")
        return result

    def plat_finalize(self, modules, py_files, extensions, dlls):
        py2exe.plat_finalize(self, modules, py_files, extensions, dlls)
        self.modules = modules

    def run(self):
        py2exe.run(self)

        script = InnoScript(self)
        print "*** creating the inno setup script ***"
        script.create()
        print "*** compiling the inno setup script ***"
        script.compile()


#
# register command
#
import distutils.command
distutils.command.__all__.append('innosetup')
sys.modules['distutils.command.innosetup'] = sys.modules[__name__]


#
# fix a problem py2exe.mf misses some modules
#
from modulefinder import packagePathMap
class PackagePathMap(object):
    def get(self, name, default=None):
        try:
            return packagePathMap[name]
        except LookupError:
            pass
        # path from Python import system
        try:
            names = name.split('.')
            for i in range(len(names)):
                modname = '.'.join(names[:i + 1])
                __import__(modname)
            return getattr(sys.modules[name], '__path__', [])[1:]
        except ImportError:
            pass
        return default
    def __setitem__(self, name, value):
        packagePathMap[name] = value
modulefinder.packagePathMap = PackagePathMap()


#
# fix a problem that `py2exe` includes MinWin's ApiSet Stub DLLs on Windows 7.
#
# http://www.avertlabs.com/research/blog/index.php/2010/01/05/windows-7-kernel-api-refactoring/
if sys.getwindowsversion()[:2] >= (6, 1):
    build_exe._isSystemDLL = build_exe.isSystemDLL
    def isSystemDLL(pathname):
        if build_exe._isSystemDLL(pathname):
            return True
        try:
            language = win32api.GetFileVersionInfo(pathname,
                '\\VarFileInfo\\Translation')
            company = win32api.GetFileVersionInfo(pathname,
                '\\StringFileInfo\\%.4x%.4x\\CompanyName' % language[0])
            if company.lower() == 'microsoft corporation':
                return True
        except Exception:
            pass
        return False
    build_exe.isSystemDLL = isSystemDLL


if __name__ == '__main__':
    sys.modules['innosetup'] = sys.modules[__name__]
    from distutils.core import setup
    setup(
        name='innosetup',
        version='0.6.3',
        license='PSF',
        description=__doc__.splitlines()[0],
        long_description=__doc__,
        author='chrono-meter@gmx.net',
        author_email='chrono-meter@gmx.net',
        url='http://pypi.python.org/pypi/innosetup',
        platforms='win32, win64',
        classifiers=[
            #'Development Status :: 4 - Beta',
            'Development Status :: 5 - Production/Stable',
            'Environment :: Win32 (MS Windows)',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: Python Software Foundation License',
            'Operating System :: Microsoft :: Windows :: Windows NT/2000',
            'Programming Language :: Python',
            'Topic :: Software Development :: Build Tools',
            'Topic :: Software Development :: Libraries :: Python Modules',
            ],
        py_modules=['innosetup', ],
        )


