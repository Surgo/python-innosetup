==========================
A Python innosetup library
==========================

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

Do the command ``setup.py innosetup``.
Then you get InnoSetup script file named ``dist\distutils.iss`` and
the installation file named ``dist\<name>-<version>.exe``.
