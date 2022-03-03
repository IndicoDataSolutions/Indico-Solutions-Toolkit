# Changelog

## 1.0.1 - 6/2/2021

### Added
* Added Snapshot merging / manipulation
* Class for highlighting extractions onto source PDFs and adding table of contents.

### Fixed
* Row Association now also sorting on 'bbtop'

## 1.0.2 6/15/2021

### Added
* PDF manipulation features
* Support for classification predictions

### Fixed
* Dependency installation


## 1.0.3 8/16/2021

### Added
* Find from questionnaire ID added to finder class.
* ModelGroupPredict support added.
* Added module to get metrics for all models in a group.
* Multi color highlighting and annotations added for PDF highlighting.
* Added stagger dataset upload feature for large doc datasets.
* Added default retry functionality for certain API calls.
* Added additional snapshot features.

### Fixed
* Wait kwarg added to submit review method.
* Better support for dataset creation / adding files to teach tasks.

## 1.0.5 9/21/2021

### Added
* Classes for model comparison and model improvement.
* Plotting functionality for model comparison.

## 1.0.7 11/9/2021

### Added
* Positioning class added to assist in relative prediction location validation
* Added # of samples labeled to metrics class.

### Removed

* Teach classes in indico_wrapper

## 1.0.8 11/15/2021

### Added
* New line plot for number of samples in metrics class.
* Update to highlighting class with new flexibility and bookmarks replacing table of contents.

## 1.1.1 12/6/2021

### Added

* Abillity to include metadata with highlighter
* Ability to split large snapshots into smaller files

## 1.1.2 12/6/2021

### Added

* Updated functionality for large dataset creation. Batch options allow for more reliable dataset uploads.

## 1.2 1/6/2022

### Added

* New distance measurements in the prediction Positioning class.
* New Features on the Extractions class: predictions that are removed by any method are saved in an 
  attribute if they're needed for logs, etc.; get all text values for a particular label; get most 
  common text value for a particular label. 
* Better exception handling for Workflow submissions and more flexibility on format of what is returned
  (allows custom response jsons to avoid the WorkflowResult class).

## 1.2.2 3/03/2022

### Added

* Updated metrics plot to order ascending based on latest model
* New feature in Positioning class to calculate overlap between two bounding boxes on the same page

### Fixed 
* Optional dependencies to support M1 installation
