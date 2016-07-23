Ascoderu webapp
===============

Development setup
-----------------

First, get the source code.

.. sourcecode :: sh

    git clone git@bitbucket.org:c-w/ascoderu-webapp.git

Second, install the dependencies for the package and verify your checkout by
running the tests.

.. sourcecode :: sh

    cd ascoderu-webapp

    virtualenv -p $(which python3) --no-site-packages virtualenv
    . virtualenv/bin/activate
    pip install -r requirements.txt

    pip install nose
    nosetests

Third, create your local database for development and seed it with some random
test data.

.. sourcecode :: sh

    touch ascoderu.db
    ./manage.py db upgrade
    ./manage.py db migrate
    ./manage.py dbpopulate
