💬 **Important**

On June 26 2024, Linux Foundation announced the merger of its financial services umbrella, the Fintech Open Source Foundation (FINOS <https://finos.org>), with OS-Climate, an open source community dedicated to building data technologies, modelling, and analytic tools that will drive global capital flows into climate change mitigation and resilience; OS-Climate projects are in the process of transitioning to the FINOS governance framework <https://community.finos.org/docs/governance>; read more on finos.org/press/finos-join-forces-os-open-source-climate-sustainability-esg <https://finos.org/press/finos-join-forces-os-open-source-climate-sustainability-esg>_

=========================
OSC Transformer Pre-Steps
=========================

|osc-climate-project| |osc-climate-slack| |osc-climate-github| |pypi| |build-status| |pdm| |PyScaffold|

OS-Climate Transformer Pre-Steps Tool
=====================================

.. _notes:

This code provides you with a cli tool with the possibility to extract data from
a pdf to a json document and to create a training data set for a later usage in the
context of transformer models
to extract relevant information, but it can also be used independently.

Quick start
============

Install via PyPi
----------------

You can simply install the package via::

    $ pip install osc-transformer-presteps

Afterwards, you can use the tooling as a CLI tool by typing::

    $ osc-transformer-presteps

We are using Typer to provide a user-friendly CLI. All details and help will be shown within the CLI itself and are not described here in more detail.

Example 1: Extracting Data from PDFs
------------------------------------

Assume the folder structure is as follows:

.. code-block:: text

    project/
    ├-input/
    │ ├-file_1.pdf
    │ ├-file_2.pdf
    │ └─file_3.pdf
    ├-logs/
    └─output/

Now, after installing ``osc-transformer-presteps``, run the following command to extract data from the PDFs to JSON::

    $ osc-transformer-presteps extraction run-local-extraction 'input' --output-folder='output' --logs-folder='logs' --force

Note: The ``--force`` flag overcomes encryption. Please check if this is a legal action in your jurisdiction.

Example 2: Curating a New Training Data Set for Relevance Detector
---------------------------------------------------------------------------

To perform curation, you will need a KPI mapping file and an annotations file. Here are examples of such files:

**KPI Mapping File**:

.. list-table:: kpi_mapping.csv
   :header-rows: 1

   * - kpi_id
     - question
     - sectors
     - add_year
     - kpi_category
   * - 0
     - What is the company name?
     - "OG, CM, CU"
     - FALSE
     - TEXT

* **kpi_id**: The unique identifier for each KPI.
* **question**: The specific question being asked to extract relevant information.
* **sectors**: The industry sectors to which the KPI applies.
* **add_year**: Indicates whether to include the year in the extracted data (TRUE/FALSE).
* **kpi_category**: The category of the KPI, typically specifying the data type (e.g., TEXT).

**Annotation File**:

.. list-table:: annotations_file.xlsx
   :header-rows: 1

   * - company
     - source_file
     - source_page
     - kpi_id
     - year
     - answer
     - data_type
     - relevant_paragraphs
     - annotator
     - sector
   * - Royal Dutch Shell plc
     - Test.pdf
     - [1]
     - 1
     - 2019
     - 2019
     - TEXT
     - ["Sustainability Report 2019"]
     - 1qbit_edited_kpi_extraction_Carolin.xlsx
     - OG

* **company**: The name of the company being analyzed.
* **source_file**: The document from which data is extracted.
* **source_page**: The page number(s) containing the relevant information.
* **kpi_id**: The ID of the KPI associated with the data.
* **year**: The year to which the data refers.
* **answer**: The specific data or text extracted as an answer.
* **data_type**: The type of the extracted data (e.g., TEXT or TABLE).
* **relevant_paragraphs**: The paragraph(s) or context where the data was found.
* **annotator**: The person or tool that performed the annotation.
* **sector**: The industry sector the company belongs to.


You can find demo files in the ``demo/curation/input`` folder.

Assume the folder structure is as follows:

.. code-block:: text

    project/
    ├-input/
    │ ├-data_from_extraction/
    │ │ ├-file_1.json
    │ │ ├-file_2.json
    │ │ └─file_3.json
    │ ├-kpi_mapping/
    │ │ └─kpi_mapping.csv
    │ ├-annotations_file/
    │ │ └─annotations_file.xlsx
    ├-logs/
    └─output/

Now, you can run the following command to curate a new training data set::

    $ osc-transformer-presteps relevance-curation run-local-curation 'input/-data_from_extraction/file_1.json' 'input/annotations_file/annotations_file.xlsx' 'input/kpi_mapping/kpi_mapping.csv'

Note: The previous comment may need some adjustment when running on different machine like windows due to the slash.


Example 3: Curating a New Training Data Set for KPI Detector
---------------------------------------------------------------------------
To perform curation, you will need the extracted json files and kpi mappinf file and annotations file (the same as described above).

Assume the folder structure is as follows:

.. code-block:: text

    project/
    ├-input/
    │ ├-data_from_extraction/
    │ │ ├-file_1.json
    │ │ ├-file_2.json
    │ │ └─file_3.json
    │ ├-kpi_mapping/
    │ │ └─kpi_mapping.csv
    │ ├-annotations_file/
    │ │ └─annotations_file.xlsx
    │ ├-relevance_detection_file/
    │ │ └─relevance_detection.csv
    ├-logs/
    └─output/

Now, you can run the following command to curate a new training data set::

    $ osc-transformer-presteps kpi-curation run-local-kpi-curation  'input/annotations_file/' 'input/data_from_extraction/' 'output/' 'kpi_mapping/kpi_mapping_file.csv' 'relevance_detection_file/relevance_file.xlsx'  --val-ratio 0.2 --agg-annotation "" --find-new-answerable --create-unanswerable

Note: The previous comment may need some adjustment when running on different machine like windows due to the slash.

.. _Important Note on Annotations:

Important Note on Annotations
-------------------------------

When performing curation, it is crucial that all JSON files used for this process are listed in the ``demo/curation/input/test_annotation.xlsx`` file. Failure to include these files in the annotation file will result in corrupted output. 

Ensure that every JSON file involved in the curation process is mentioned in the annotation file to maintain the integrity of the resulting output.


Developer space
================

Use Code Directly Without CLI via Github Repository
-----------------------------------------------------

First, clone the repository to your local environment::

    $ git clone https://github.com/os-climate/osc-transformer-presteps

We are using ``pdm`` to manage the packages and ``tox`` for a stable test framework.
First, install ``pdm`` (possibly in a virtual environment) via::

    $ pip install pdm

Afterwards, sync your system via::

    $ pdm sync

You will find multiple demos on how to proceed in the ``demo`` folder.

pdm
---

To add new dependencies, use ``pdm``. For example, you can add numpy via::

    $ pdm add numpy

For more detailed descriptions, check the `PDM project homepage <https://pdm-project.org/en/latest/>`_.

tox
---

For running linting tools, we use ``tox``. You can run this outside of your virtual environment::

    $ pip install tox
    $ tox -e lint
    $ tox -e test

This will automatically apply checks on your code and run the provided pytests. See more details on `tox <https://tox.wiki/en/4.16.0/>`_.

.. |osc-climate-project| image:: https://img.shields.io/badge/OS-Climate-blue
  :alt: An OS-Climate Project
  :target: https://os-climate.org/

.. |osc-climate-slack| image:: https://img.shields.io/badge/slack-osclimate-brightgreen.svg?logo=slack
  :alt: Join OS-Climate on Slack
  :target: https://os-climate.slack.com

.. |osc-climate-github| image:: https://img.shields.io/badge/GitHub-100000?logo=github&logoColor=white
  :alt: Source code on GitHub
  :target: https://github.com/ModeSevenIndustrialSolutions/osc-transformer-presteps

.. |pypi| image:: https://img.shields.io/pypi/v/osc-transformer-presteps.svg
  :alt: PyPI package
  :target: https://pypi.org/project/osc-transformer-presteps/

.. |build-status| image:: https://api.cirrus-ci.com/github/os-climate/osc-transformer-presteps.svg?branch=main
  :alt: Build Status
  :target: https://cirrus-ci.com/github/os-climate/osc-transformer-presteps

.. |pdm| image:: https://img.shields.io/badge/PDM-Project-purple
  :alt: Built using PDM
  :target: https://pdm-project.org/latest/

.. |PyScaffold| image:: https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold
  :alt: Project generated with PyScaffold
  :target: https://pyscaffold.org/
