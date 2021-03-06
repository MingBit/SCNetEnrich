[![Codacy Badge](https://api.codacy.com/project/badge/Grade/d3c17aac77e14f6bb17b33f875ff7471)](https://app.codacy.com/manual/MingBit/PySCNet?utm_source=github.com&utm_medium=referral&utm_content=MingBit/PySCNet&utm_campaign=Badge_Grade_Dashboard)
[![License](https://img.shields.io/github/license/MingBit/PySCNet)](https://github.com/MingBit/PySCNet/blob/master/LICENSE)
[![Build Status](https://travis-ci.org/MingBit/PySCNet.svg?branch=master)](https://travis-ci.org/MingBit/PySCNet)
[![Documentation Status](https://readthedocs.org/projects/pyscnet/badge/?version=latest)](https://pyscnet.readthedocs.io/en/latest/?badge=latest)

# PySCNet: A tool for reconstructing and analyzing gene regulatory network from single-cell RNA-Seq data
There are four modules:
1) **Pro-precessing**: initialize a gnetData object consisting of Expression Matrix, Cell Attributes, Gene Attributes and Network Attributes;
2) **BuildNet**: reconstruct GRNs by various methods implemented in docker;
3) **NetEnrich**: network analysis including consensus network detection, gene module identification and trigger path prediction as well as network fusion;
4) **Visulization**: network illustration.

![Overview](https://github.com/MingBit/PySCNet/blob/master/images/Overview.png)

# :tada: :confetti_ball: Create your own GRNs
[Dashboard](https://github.com/MingBit/PySCNet/blob/master/images/pyscnet_dashboard.gif) is available now for creating your own GRNs.
Cell specific GRNs and network analysis results can be saved as a pickle object and upload onto PySCNet-Dashboard.
It provides parameter settings and allows for parameter adjustment and GRNs customization. <br/>
To run the python dashboard: <br/>
`cd PySCNet/pyscnet/dash_pyscnet/` <br/>
`python app.py` 


# Installation
Make sure you have [Docker](https://docs.docker.com/engine/install/ubuntu/) and [graph_tool](https://git.skewed.de/count0/graph-tool/-/wikis/installation-instructions) manually installed. <br/>
`conda create --name gt -c conda-forge graph-tool python=3.6` <br/>
`conda activate gt`

1) clone from github:
`git clone https://github.com/MingBit/PySCNet`
2) create a new folder and set up:
`mkdir dist | python setup.py sdist`
3) install pyscnet:
`pip install dist/pyscnet-0.0.3.tar.gz`

# Tutorial
Make sure you have [scanpy](https://scanpy.readthedocs.io/en/stable/installation.html) and [stream](https://github.com/pinellolab/STREAM) manually installed. <br/>
`pip install jupyterlab scanpy==1.5.0` <br/>
`conda install -c bioconda stream` <br/>

You might need to re-install anndata: `pip install anndata==0.7.4`

Mouse HSC data preprocessed and analyzed by stream as explained in this 
[tutorial](https://github.com/MingBit/PySCNet/blob/master/tutorial/pyscnet_stream.ipynb). 

open jupyter-notebook with `/miniconda3/envs/gt/bin/./jupyter-notebook ~/PySCNet/tutorial/pyscnet_stream.ipynb `

# TO-DO
1) Add an Auto-ML based pipeline to Pre-Processing module;
2) Collect more GRN methods to BuildNet module;
3) Update network fusion algorithms to NetEnrich module;
5) Test with integrated sc RNA-seq data.

# Cite
- :smile_cat: This work has been presented at [ISMB/ECCB 2019](https://www.iscb.org/ismbeccb2019);
- :paw_prints: Go to [my poster](https://f1000research.com/posters/8-1359);
- :page_with_curl: Reference: *Wu M, Kanev K, Roelli P and Zehn D. PySCNet:
A tool for reconstructing and analyzing gene regulatory network from single-cell RNA-Seq data [version 1; not peer reviewed]. F1000Research 2019, 8(ISCB Comm J):1359 (poster) (doi: 10.7490/f1000research.1117280.1)*
