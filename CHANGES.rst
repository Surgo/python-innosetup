Changes
-------

0.6.6, 0.6.7
^^^^^^^^^^^^

* update readme.

0.6.5
^^^^^

* move download url to github.

0.6.4
^^^^^

* move repository to github.
* add a setup.py script.

0.6.3
^^^^^

* change versioning policy (remove build number).
* add utf-8 bom to .iss file by Jerome Ortais, thanx.
* pick up `COPYING` file for `[setup]/LicenseFile` by Jerome Ortais, thanx.

0.6.0.2
^^^^^^^

* add `regist_startup` option for create shortcut to startup.

0.6.0.1
^^^^^^^

* fix metadata and unicode by surgo, thanx.
* set `DEFAULT_ISS` to empty because `Inno Setup 5.3.9` is released.
* fix a problem that `py2exe` includes MinWin's ApiSet Stub DLLs on Windows 7.

0.6.0.0
^^^^^^^

* support bundling tcl files
* change OutputBaseFilename

0.5.0.1
^^^^^^^

* improve update install support

0.5.0.0
^^^^^^^

* add DEFAULT_ISS, manifest, srcname, srcnames
* add `zip` option
* fix `bundle_files=1` option problem (always bundle pythonXX.dll)
* add `DefaultGroupName`, `InfoBeforeFile`, `LicenseFile` into `[Setup]`
  section

0.4.0.0
^^^^^^^

* support service cmdline_style options
* rewrite codes around iss file

0.3.0.0
^^^^^^^

* improve the InnoSetup instllation path detection
* add `inno_setup_exe` option

0.2.0.0
^^^^^^^

* handle `py2exe`'s command options
* add `bundle_vcr` option

0.1.0.0
^^^^^^^

* first release
