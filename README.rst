=====================================================================
OSC Data Extractor Pre-Steps
=====================================================================

|osc-climate-project| |osc-climate-slack| |osc-climate-github| |pypi| |build-status| |pdm| |PyScaffold|

OS-Climate Data Extraction Tool
===============================

.. _notes:

This code provides you with an api and a streamlit app to which you
can provide a pdf document and the output will be the text content in a json format.
In the backend it is using a python module for extracting text from pdfs, which
might be extended in the future to other file types.
The json file is needed for later usage in the context of transformer models
to extract relevant information, but it can also be used independently.

Quick start
===========

Install via PyPi
----------------

You can simply install the package via::

    $ pip install osc-transformer-presteps

Afterwards you can use the tooling as a CLI tool by simply typing::

    $ osc-transformer-presteps

We are using typer to have a nice CLI tool here. All details and help will be shown in the CLI
tool itself and are not described here in more detail.


Install via Github Repository
-----------------------------

For a quick start with the tool install python and clone the repository to your local environment::

    $ git clone https://github.com/os-climate/osc-transformer-presteps

Afterwards update your python to the requirements (possible for example
via pdm update) and start a local api server via::

    $ python ./src/run_server.py

**Note**:
    * We assume that you are located in the cloned repository.
    * To check if it is running open "http://localhost:8000/liveness" and you should see the
      message {"message": "OSC Transformer Pre-Steps Server is running."}.

Finally, run the following code to start a streamlit app which opens up the possibility
to "upload" a file and extract data from pdf to json via this UI. Note that the UI needs
the running server so you have to open the streamlit and the server in two different
terminals.::

    $ streamlit run ./src/osc_transformer_presteps/streamlit/app.py

**Note**: Check also docs/demo. There you can
find local_extraction_demo.py which will start an extraction
without any API call and then there is post_request_demo.py
which will send a file to the API (of course you have to start
server as above first).

Developer Notes
===============

For adding new dependencies use pdm. First install via pip::

    $ pip install pdm

And then you could add new packages via pdm add. For example numpy via::

    $ pdm add numpy

For running linting tools just to the following::

    $ pip install tox
    $ tox -e lint
    $ tox -e test


.. |osc-climate-project| image:: https://img.shields.io/badge/OS-Climate-blue
  :alt: An OS-Climate Project
  :target: https://os-climate.org/

.. |osc-climate-slack| image:: https://img.shields.io/badge/slack-osclimate-brightgreen.svg?logo=slack
  :alt: Join OS-Climate on Slack
  :target: https://os-climate.slack.com

.. |osc-climate-github| image:: https://img.shields.io/badge/GitHub-100000?logo=github&logoColor=white
  :alt: Source code on GitHub
  :target: https://github.com/ModeSevenIndustrialSolutions/osc-data-extractor

.. |pypi| image:: https://img.shields.io/pypi/v/osc-data-extractor.svg
  :alt: PyPI package
  :target: https://pypi.org/project/osc-data-extractor/

.. |build-status| image:: https://api.cirrus-ci.com/github/os-climate/osc-data-extractor.svg?branch=main
  :alt: Built Status
  :target: https://cirrus-ci.com/github/os-climate/osc-data-extractor

.. |pdm| image:: https://img.shields.io/badge/PDM-Project-purple
  :alt: Built using PDM
  :target: https://pdm-project.org/latest/

.. |PyScaffold| image:: https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold
  :alt: Project generated with PyScaffold
  :target: https://pyscaffold.org/
