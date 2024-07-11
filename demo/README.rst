=====================================================================
DEMO Scripts Overview
=====================================================================

.. _notes:

In this folder you can find multiple demo scripts on how to use the python scripts in
different ways beside the *normal* CLI tool.

**Note**:

* We assume that you are located in an environment where you have
  already installed the necessary requirements (see initial readme).

* The demos are not part of the tox setup and the tests. Hence, it might be that some
  packages or code parts can be outdated. Those are just ideas on how to use and not
  prod ready. Feel free to inform us nevertheless if you encounter issues with the demos.


extraction_api
....................

This demo is an implementation of the code via FastAPI. In api.py the API is created and the
extraction route is build up in extract.py. To start the server run:

    $ python demo/extraction_api/api.py

Then the server will run and you can test in your browser that it worked at:

    http://localhost:8000/liveness

You should see the message {"message": "OSC Transformer Pre-Steps Server is running."}.

extraction
....................

This demo has two parts to extract data from the input folder to the output folder.

a) The post_request_extract.py is using the api endpoint from extraction_api to send a
file to the api via a post request and receives the output via an api respons. The file
you want to extract can be entered in the cmd line:

    $ python demo/extraction/post_request_extract.py

b) The local_extraction_demo.py runs the extraction code directly for Test.pdf file.
If you want to use another file you have to change that in the code.

extraction_streamlit
....................

This is an example implementation of a streamlit app which opens up the possibility
to "upload" a file and extract data from pdf to json. Note that the UI needs
the running server from extraction_api and so you have to open the streamlit
and the server in two different terminals. An example file to upload can be found in
"/demo/extraction/input". You can start the streamlit via:

    $ streamlit run ./src/osc_transformer_presteps/extraction_streamlit/app.py

curation
....................

T.B.D.
