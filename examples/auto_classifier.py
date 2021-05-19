from indico_toolkit.auto_class import AutoClassifier, FirstPageClassifier
from indico_toolkit import create_client

HOST = "app.indico.io"
API_TOKEN_PATH = "./indico_api_token.txt"
PATH_TO_DIR = "./base_directory/"


client = create_client(HOST, API_TOKEN_PATH)
"""
EXAMPLE 1:

Create a CSV that can be used to train a document classification model without any labeling 
using an organized directory/folder structure. Each folder/directory should contain only one file 
type.

For example, you would target '/base_directory/' if you had your files organized like:

/base_directory/
/base_directory/invoices/ -> contains only invoice files
/base_directory/disclosures/ -> contains only disclosure files

"""
autoclass = AutoClassifier(client, PATH_TO_DIR)
autoclass.set_file_paths(accepted_types=("pdf", "tiff"))
autoclass.create_classifier(verbose=True, batch_size=5)
autoclass.to_csv("./auto_classifier.csv")

"""
EXAMPLE 2:

Create a CSV that can be used to train a first page classification model without any labeling.

A First Page Classifier enables you to identify the first page of documents and to split 
apart bundled documents whenever a 'first page' occurs in the bundle. The files in your
'directory_path' should contain NO bundled documents, i.e. every PDF should be comprised of 
1 unique document, NOT multiple unique documents.

"""
pageclass = FirstPageClassifier(client, PATH_TO_DIR)
# You can optionally search for files in 'PATH_TO_DIR' recursively
pageclass.set_file_paths(recursive_search=True)
pageclass.create_classifier(verbose=True, batch_size=5)
pageclass.to_csv("./first_page_classifier.csv")
