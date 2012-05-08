.. -*- restructuredtext -*-

==========================
A Python innosetup library
==========================
distutils extension module - create an installer by InnoSetup.
--------------------------------------------------------------

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

Example
-------
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
the installation file named `dist\<name>-<version>.exe`.


History
-------
0.6.3
~~~~~

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
