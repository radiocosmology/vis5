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

HDF5 has many advanced features for controlling how its data are stored, but it is
worth highlighting two:

- Chunking: rather than storing data as a monolithic blob on disk, HDF5 can break a
dataset up into arbitrary sized n-dimensional chunks that tile the n-dimensional
dataset, each of which is stored contiguously. This allows much faster IO for access
patterns that stride the dataset.
- Filtering: when a dataset is chunked it is also possible to apply filters to it.
These filters can apply arbitrary transforms on the data as they are read and written
such as compression.


### Caput Container Conventions

HDF5 is in many ways is a *meta-format*. It gives a mechanism for defining encoding
arbitrary multi-dimensional datasets within a single file, along with their metadata.
However, to produce a usable file format for a specification application we need to
further specify how these data are structured within the file, things like dataset
names, required metadata, types of datasets.

This file format adopts the conventions used within the `BasicCont` type of the
[caput](https://github.com/radiocosmology/caput/) to ensure that the data are fairly
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

Vis5 files are designed to store visibility data from telescopes like CHIME, alongside
all the data that are needed to understand them, such as metadata about what was
being observed, noise estimates, applied gains, feeds that were flagged out.
Additionally this format is designed to support *stacked* visibilities that have been
averaged redundant baselines.

Unless explicitly specified all the entries below are **required** within a compliant
Vis5 file.


### Datatypes

We specify the datatypes required for both the datasets and axis definitions below.
For readability we use the following shorthands, which are defined in terms of the
fundamental HDF5 types as:
- `BOOL`: `H5T_STD_U8LE` with 0 meaning False and > 0 meaning True (though 1 is the
  preferred value).
- `UINT16`: `H5T_STD_U16LE`
- `UINT32`: `H5T_STD_U32LE`
- `UINT64`: `H5T_STD_U64LE`
- `FLOAT64`: `H5T_IEEE_F64LE`
- `COMPLEX64` A single precision complex number. This is a *compound datatype*
  consisting of two entries:
    * `r` (type: `H5T_IEEE_F32LE`): the real part of the complex number
    * `i` (type: `H5T_IEEE_F32LE`): the imaginary part of the complex number
  Note that this is the same format used by `h5py` to store complex numbers, and so
  should allow native reading of the datasets into Python.

If a datatype is written as `min <type>` that means any datatype of equivalent type
and equal or higher precision is acceptable. For instance for `min UINT32` the
datatype `UINT64` would be compliant, but not the datatype `UINT16`, nor `FLOAT64`.

### Axes

Each axis must have an entry under `/index_map/`.

#### time

This axis gives the **start** time of each sample in an acquisition.

It must consist of a datatype of two entries:
- `fpga_count` (type: `UINT64`): an integer sequence number for the output from the
  correlator. This should be an exact counter with no rounding. *NOTE*: for
  historical reasons this entry is named `fpga_count` and though using this name is
  **strongly** recommended, it is not required, and the implementer may choose any
  *appropriate name.
- `ctime` (type: `FLOAT64`): the UTC time since the UNIX epoch in floating point seconds.

#### freq

The frequency in physical units of each observed channel.

It must consist of a datatype of two entries:
- `centre` (type: `FLOAT64`): the "centre" of the frequency channel in MHz.
- `width` (type: `FLOAT64`): the "width" of the frequency channel in MHz.

Frequency channels may have complex shapes depending on exactly how the
channelisation was performed. The exact definition of "centre" and "width" for a
telescope is left up to the implementer.

#### input

This describes each input to the correlator.

It must consist of a datatype of two entries:
- `chan_id` (type: `min UINT16`): an integer ID assigned to each input channel.
- `correlator_input` (type: length 32 ASCII string): a string label (e.g. a serial
  number for each input).

#### prod

This describes inputs that have been combined into a correlation product.

It must consist of a datatype of two entries:
- `input_a` (type: `min UINT16`): the first input in the correlation. This is
given as an index pointing into the `input` axis.
- `input_b` (type: same as for `input_a`): the second input in the correlation given as an
index into the `input` axis.

By convention the first input (a) is the unconjugated, and the second (b) carries the
complex conjugation.

#### stack

**OPTIONAL**: required only if the visibilities have been stacked.

The stack axis describes how redundant visibilities have been added together. Each
entry points to the index of a typical product that would have been averaged into the
stack, and whether it would need to have been complex conjugated before averaging.

This must consist of a datatype of two entries:
- `prod` (type: `UINT32`): an index into the `prod` axis that gives a product
  equivalent to this stacked visibility.
- `conjugate` (type: `BOOL`): whether the product must
  be conjugated (equivalent to reversing its `input_a`/`input_b` entries) for the stack
  to be equivalent.

Note, in addition to the `stack` index map, it is highly recommended (required????)
to have a `/reverse_map/stack` dataset. This allows us to explicitly identify which
products have been averaged into a particular stack output. It is a dataset the
length of the product axis, and for each product points to which stack entry it was
placed in. If present, this must consist of a datatype with two entries:
- `stack` (type: `UINT32`): an index into the stacked axis which points to the
  stack entry this product was averaged into.
- `conjugate` (type: `BOOL` interpreted as boolean): whether the product must
  be conjugated before being added to the stack.

(NOTE: what about entries that aren't stacked????)

#### ev

**OPTIONAL**: required only if there are [`eval`](#eval) or [`evec`](#evec) datasets present.

This denotes different eigenmodes of the data. The eigenmodes are in *descending* order.

It must consist of a datatype with a single entry `UINT32` entry giving the
eigenvalue number (indexed from zero in descending order).


### Datasets

Unless otherwise noted, the following datasets are all required for a compliant file.
The title for each entry gives the path relative to the file root.

#### vis

- Axes: `(freq, [prod|stack], time)`
- Datatype: `COMPLEX64`

The visibilities for the data. As specified above, the visibilities are assumed to
have conjugation convention:
$$V_{ab}(\nu, t) = \left\langle x_a(\nu, t) x_b(\nu, t)^* \right\rangle$$


#### gain

- Axes: `(freq, input, time)`
- Datatype: `COMPLEX64`

The gain that was *applied* to each correlator input. The exact interpretation of
this gain, and the intended calibration of the visibility data for the telescope is
left up to the implementer.


#### flags/vis_weight

- Axes: same as `/vis`
- Datatype: `FLOAT32`

An estimate of the "weight" of each piece of data. Weight is defined as the *inverse
variance* of each entry of the visibility dataset. Note that in this definition, a
weight of zero corresponds to infinite variance and is thus used to denote *missing*
data.


#### flags/input

- Axes: `(input, time)`
- Datatype: `FLOAT32`

The weight a given input should be given. This is used to indicate the integrity of
each input with time and give it a weighting. This is most important when the data
have been redundant baseline averaged (and thus have a `stack` axis), and should be
interpreted as the relative weight given to each input in the redundant baseline
averaging procedure. If a feed has weight zero, that should be interpreted as a "bad"
input and no correlation product using it would be included in the stacked output.


#### flags/frac_lost

- Axes: `(input, time)`
- Datatype: `FLOAT32`

The fraction of data for each freq-time sample that has been lost for *any* reasons.
This is used to determine the true integration time of each sample. It is assumed to
be *independent* of input or product.


#### flags/frac_rfi

**OPTIONAL**

- Axes: `(input, time)`
- Datatype: `FLOAT32`

The fraction of data for each freq-time sample that has been lost for solely due to
RFI flagging. Any flagging here must be included within [`flags/frac_lost`] such that
the corresponding entry in that dataset must be equal to or larger than the entry
here. This is used for monitoring the RFI environment, and is again assumed to be
*independent* of input or product.


#### eval

**OPTIONAL**

- Axes: `(freq, ev, time)`
- Datatype: `FLOAT32`

The eigenvalue of the decomposed correlation matrix.


#### evec

**OPTIONAL**

- Axes: `(freq, ev, input, time)`
- Datatype: `COMPLEX64`

The eigenvectors of the decomposed correlation matrix.


#### erms

**OPTIONAL**

- Axes: `(freq, time)`
- Datatype: `FLOAT32`

The root-mean-square of the remaining eigenvalues of the matrix. This is related to
the average residual between the correlation matrix and the rank-*N* approximation
formed from the *N* eigenvalues returned.


#### flags/dataset_id

**OPTIONAL**

- Axes: `(freq, time)`
- Datatype: length-32 string interpreted as a hexadecimal string hash

This is a unique identifier identify the set of transformations that have been done
to the data. Although this can in theory be filled in an arbitrary way by the
implementer it is designed to be used by the Dataset Manager framework within
`kotekan`. Within that framework the dataset ID is derived from a 128-bit hash that
identifies the full set of transformations that have been done to the data.
Dynamically changing parameters like the RFI flagging, or updating the flagged inputs
all represent distinct transformations and will thus cause the data to be given
distinct dataset IDs.



## Recommendations

### Compression and Filtering


### Stack order for CHIME

The visibility datasets can now have a stack axis where before they would only have
had a prod axis. This axis is sorted lexicographically by the key (pol1, pol2, cyl1,
cyl2, feed_sep_NS). For example the first entry should correspond to (pol X, pol X,
cyl A, cyl A, 0 feed sep NS) i.e. XX autos on Cyl A; the next entry would be (pol X,
pol X, cyl A, cyl A, +1 feed sep NS) ...

All stacked baselines are constructed such that they point towards the East (or for
within cylinder baselines, point North).
