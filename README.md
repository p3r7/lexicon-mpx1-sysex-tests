# lexicon-mpx1-sysex-tests

Small python scripts to remote control a MPX1 over midi.

The aim is to provide functionality similar to a Lexixon [MRC](https://lexiconpro.com/en/products/mrc) or [LARC](https://lexiconpro.com/en/products/larc).


## Setup

Those script are made to run under a conda virtual env created with the provided [environment.yml](./environment.yml) file.

To initialize it:

    conda env create
    conda activate lexicon-mpx1-sysex-tests-env

To not depend on jack, the scripts use the `pygame` mido backend.

Under Ubuntu, this was necessary:

    yes | sudo apt install libasound2-plugins
    cd /usr/lib/x86_64-linux-gnu/
    sudo ln -s alsa-lib/libasound_module_conf_pulse.so libasound_module_conf_pulse.so
    cd -


## Documentation

https://mido.readthedocs.io/en/latest/messages.html#system-exclusive-messages

https://lexiconpro.com/en/product_documents/mpx1_v1_1_midi_impl_rev1pdf

https://www.linuxrouen.fr/wp/programmation/scripts-midi-in-avec-python-mido-et-rtmidi-25420/

https://www.youtube.com/watch?v=lszMkl3Jp1k&t=1218s

https://github.com/vishnubob/python-midi/issues/95#issuecomment-246513542
