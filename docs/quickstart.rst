Quickstart
==========

Install
-------

.. code-block:: bash

   make install        # pip install -r requirements-dev.txt
   make run            # starts the dev server on http://localhost:5000

Or with Docker:

.. code-block:: bash

   docker build -t flask-cicd-demo .
   docker run -p 5000:5000 flask-cicd-demo

Try the API
-----------

Create a task:

.. code-block:: bash

   curl -X POST http://localhost:5000/api/tasks \
        -H "Content-Type: application/json" \
        -d '{"title": "Buy groceries"}'
   # -> 201  {"id": 1, "title": "Buy groceries", "done": false}

List tasks:

.. code-block:: bash

   curl http://localhost:5000/api/tasks
   # -> 200  {"tasks": [...], "count": 1}

Mark a task as done:

.. code-block:: bash

   curl -X PUT http://localhost:5000/api/tasks/1 \
        -H "Content-Type: application/json" \
        -d '{"done": true}'

Delete a task:

.. code-block:: bash

   curl -X DELETE http://localhost:5000/api/tasks/1
   # -> 200  {"message": "task deleted"}

See the :doc:`api` page for the full, auto-generated endpoint reference.
