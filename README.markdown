PyPack: A Production Package Builder for Python
===============================================

Background
----------
Pypack is a packaging system designed for large python projects.

Pypack will read "build" definition files that you write, and bundle the transitive
closure of module dependencies into a zip file, and output a wrapped binary to execute.
This is very similar in concept to Java's .jar packaging and execution format.


Pypack was designed more for teams working on projects than people distributing
open-source software. It's inspired by Google's internal build system, in which
a developer lists his dependencies, and the build system will put it all together
in one big ball, to be deployed as a self-contained unit.


Why not virtualenv?
-------------------

Python's virtual environment system is somewhat misdirected for corporate teams,
especially those that use third party libraries. Virtualenv works almost like chroot,
giving you a $ENV/lib/pythonX.X/site-packages directory that you can direct pip
or easy_install to drop packages in.

However, the realities of working with a team and referencing third party libraries
often require you to check your libraries into source control, and designate one team
member as the internal maintainer of that package.

Pypack facilitates that workflow, as when you check a third party package into
source control, you can put all your company's metadata in the build definition
file in that library's source folder.

This way, you don't get production ImportErrors and have to go around asking your
team what pip package to install. Plus, it leaves fewer room for errors with conflicting
versions of third party libraries.

Pypack also allows different parts of your codebase to run against different
versions of third-party libraries. Simply declare your dependency on the given
version, build the package, and run it on whatever machine you like.


Usage
-----

Suppose you have a codebase laid out like this:

<pre>
codebase/
  webapp/
    views/
    controllers/
    serve.py
  db_models/
  backend/
    feed_fetcher/
      fetch_feeds.py
    spam_detector/
      detect_spam.py
  util/
    net/
    database/
  third_party/
    lxml/
    mechanize/
</pre>

There are a few distinct applications here, the webapp, and some backend programs.
Each application imports things from db_models, util, and third_party.

You would define a PYPACK file for the webapp like this:

```cfg
[project]
name = webapp

[depends]
db_models
third_party/lxml
util/database

[binaries]
serve = serve.py
```

Put this file in codebase/webapp/PYPACK, and run the following:

```console
python pypack.py webapp/
```

Pypack will output two files, an executable ```webapp```, and its self-contained
dependencies, ```webapp.zip```.


License
-------

Pypack is released under the Apache License, Version 2.0