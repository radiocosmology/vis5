# Visibility data specification

Modern radio interferometers generate extremely large datasets that need to be stored for later analysis.

This document is a specification for the visibility data format used by [CHIME](https://chime-experiment.ca/) and [HIRAX](https://hirax.ukzn.ac.za). It is based around [HDF5](https://hdf5.org/) a library and file-format for storing large volumes of structured binary data along with it's metadata

## Container Conventions

HDF5 is in many ways is a *meta-format*. It gives a mechanism for defining encoding arbitrary multi-dimensional datasets within a single file, along with their metadata. However, to produce a usable file format for a specification application we need to further specify how this data is structured within the file, things like dataset names, required metadata, types of datasets.

### HDF5 Concepts

HDF5 files allow the hierarchial storage of multiple **datasets** within a single file, each dataset is an n-dimensional array of a fixed datatype

- Datatype: the item type within a dataset. This may be a fundamental type like a 32-bit floating point number, a 64-bit integer, or a unicode string; or it may be a compound type such as a pair of 32-bit integers representing a single precision complex number.
- Attribute: a simple key-value pair representing metadata.
- Dataset: an n-dimensional array of items of fixed datatype. Datasets may be tagged with metadata.
- Groups: a directory-like structure that can contain datasets or other groups.

This file format uses the conventions enforced by the `BasicCont` type of the [caput](https://github.com/radiocosmology/caput/) to further pin this down.

