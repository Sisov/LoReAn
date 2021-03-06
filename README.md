# LoReAn (Long Read Annotation) for automated eukaryotic genome annotation incorporating long-reads

The LoReAn software is an automated annotation pipeline designed for eukaryotic genome annotation. It is built using previously 
defined annotation rationale and programs, but the key improvement is the incorporation of single-molecule cDNA sequencing data, 
such as that produced from [Oxford Nanopore](https://nanoporetech.com/) and from [PacBio](http://www.pacb.com/applications/rna-sequencing/). 
We find this significantly improves automated annotations and reduces the requirments for time-consuming manual annotation. 

We are working to improve LoReAn documentation. Meanwhile, some more LoReAn information can be found at 
[bioRxiv](https://www.biorxiv.org/content/early/2017/12/08/230359). For those familar with the annotation process and 
with docker, there should be enough infomation to run the program. If you have problems, please open an issue.

This is how LoReAn works: [LoReAn schematic view](https://github.com/lfaino/LoReAn/wiki)

## HOW TO RUN

LoReAn requires three mandatory files:
* Protein Sequences
* Reference genome sequence 
* Genome name

To install the software:

Please see the [installation instructions](INSTALL.md) for details. 

The software can be run after installing by:
```bash
lorean.py -pr protein.fasta -sp spacies genome.fasta 
```
The full list of options can be found at [option instructions](OPTIONS.md) or by:

```bash
lorean.py --help
```

LoReAn can run BRAKER to improve Augustus gene prediction;

To do so, short reads from RNA-seq or long reads RNA-seq need to be provided

## EXAMPLE DATASET

We made available two datasets that can be used to test LoReAn. The 1st dataset is from Nanopore data of *Verticillium dahliae* 
strain JR2 while the second is from PacBio data of *Plicaturopsis crispa*. Both datasets can be dowloaded from 
[LoReAn Examples ](https://github.com/lfaino/LoReAn_Example)


## SOFTWARE USED IN THE PIPELINE


- TransDecoder-3.0.1
- samtools v0.1.19-96b5f2294a
- bedtools v2.25.0
- bowtie  v1.1.2
- bamtools v2.4.1
- AATpackage r03052011 
- iAssembler v1.3.2.x64
- GeneMark-ES/ET v.4.33 64bit **(THIS SOFTWARE IS NOT FREE FOR EVERYONE, check installation instruction)** 
- PASApipeline v2.1.0 
- augustus v3.3
- trinityrnaseq v2.5.1
- STAR v2.5.3a
- gmap-gsnap v2017-06-20
- fasta v36.3.8e
- BRAKER v2.0
- EVidenceModeler v1.1.1
- gffread  v0.9.9
- genometools v1.5.9


## AUTHORS:
- Luigi Faino
- David Cook
- Jose Espejo


