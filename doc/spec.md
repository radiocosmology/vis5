# Visibility data specification

Modern radio interferometers generate extremely large datasets that need to be stored
for later analysis.

This document is a specification for the visibility data format used by
[CHIME](https://chime-experiment.ca/) and [HIRAX](https://hirax.ukzn.ac.za). It is
based around [HDF5](https://hdf5.org/) a library and file-format for storing large
volumes of structured binary data along with it's metadata

## Preliminaries

### HDF5 Concepts

HDF5 files allow the hierarchial storage of multiple *datasets* within a single
file.

- Datatype: the item type within a dataset. This may be a fundamental type like a
  32-bit floating point number, a 64-bit integer, or a unicode string; or it may be a
  compound type such as a pair of 32-bit integers representing a single precision
  complex number.
- Attribute: a simple key-value pair representing metadata.
- Dataset: an n-dimensional array of items of fixed datatype. Datasets may be tagged
  with metadata.
- Groups: a directory-like structure that can contain datasets or other groups.

A file represents a tree like structure with the file start point the root, datasets
located at the leaves and groups at any intermediate position. Paths within HDF5
files are typically listed as a UNIX file path would be, e.g.
`/group1/group2/dataset`.

HDF5 has many advanced features for controlling how its data is stored, but it is
worth highlighting two:

- Chunking: rather than storing data as a monolithic blob on disk, HDF5 can break a
dataset up into arbitrary sized n-dimensional chunks that tile the n-dimensional
dataset, each of which is stored contiguously. This allows much faster IO for access
patterns that stride the dataset.
- Filtering: when a dataset is chunked it is also possible to apply filters to it.
These filters can apply arbitrary transforms on the data as it is read and written
such as compression.


### Caput Container Conventions

HDF5 is in many ways is a *meta-format*. It gives a mechanism for defining encoding
arbitrary multi-dimensional datasets within a single file, along with their metadata.
However, to produce a usable file format for a specification application we need to
further specify how this data is structured within the file, things like dataset
names, required metadata, types of datasets.

This file format adopts the conventions used within the `BasicCont` type of the
[caput](https://github.com/radiocosmology/caput/) to ensure that the data is fairly
self-documented. These are:

- Datasets must have named axes representing each dimension. The names of these axes
  must be given as a `axis` attribute on the dataset itself. For instance a `/gain`
  dataset might be three-dimensional with the axes in order being `["freq", "input", "time"]`,
  which should be the value in the `axis` attribute. Every dataset must have
  the same length across dimensions which have matching axis labels.
- Each axis must be described by an *index_map*. This is a one-dimensional dataset
  located at `/index_map/<axis_name>` which has the same length as the corresponding
  dimension in every matching dataset. Each element in the index_map for the axis gives
  a description of what that index means. For example a file may have datasets with a
  `"time"` axis, the `/index_map/time` entry may be an array of floating point numbers
  with each giving the UNIX timestamp corresponding to the acquisition time of each
  sample in the time series.


## Vis5 specification

Vis5 files are designed to store visibility data from telescopes like CHIME, along
side all the data that is needed to understand them, such as metadata about what was
being observed, noise estimates, applied gains, feeds that were flagged out.
Additionally this format is designed to support *stacked* visibilities that have been
averaged redundant baselines.

Unless explicitly specified all the entries below are **required** within a compliant
Vis5 file.

### Axes

Each axis must have an entry under `/index_map/`. Unless mentioned

#### time

This axis gives the **start** time of each sample in an acquisition.

It must consist of a datatype of two entries:
- `fpga_count` (type: `H5T_STD_U64LE`): an integer sequence number for the output from the correlator. This should be an exact counter with no rounding.
- `ctime` (type: `H5T_IEEE_F64LE`): the UTC time since the UNIX epoch in floating point seconds.

#### freq

The physical frequency of each observed channel.

It must consist of a datatype of two entries:
- `centre` (type: `H5T_IEEE_F64_LE`): the "centre" of the frequency channel in MHz.
- `width` (type: `H5T_IEEE_F64_LE`): the "width" of the frequency channel in MHz.

Frequency channels may have complex shapes depending on exactly how the
channelisation was performed. The exact definition of "centre" and "width" for a
telescope is left up
to the implementer.

#### input

This describes each input to the correlator.

It must consist of a datatype of two entries:
- `chan_id` (type: `H5T_STD_U16LE`): an integer ID assigned to each input channel.
- `correlator_input` (type: length 32 ASCII string): a string label (e.g. a serial number for each input).

#### prod

This describes which the inputs that have been combined into a correlation product.

It must consist of a datatype of two entries:
- `input_a` (type: `H5T_STD_U16LE`): the first input in the correlation. This is
given as an index pointing into the `input` axis.
- `input_b` (type: `H5T_STD_U16LE`): the second input in the correlation given as an
index into the `input` axis.

By convention the first input (a) is the unconjugated, and the second (b) carries the
complex conjugation.

#### stack

**OPTIONAL**: required only if the visibilities have been stacked.

The stack axis describes how redundant visibilities have been added together.

