# lexicon-mpx1-sysex-tests

Small python scripts to remote control a MPX1 over midi.

The aim is to provide functionality similar to a Lexixon [MRC](https://lexiconpro.com/en/products/mrc) or [LARC](https://lexiconpro.com/en/products/larc).


## Setup

Those script are made to run under a conda virtual env created with the provided [environment.yml](./environment.yml) file.

To initialize it (conda):

    conda env create
    conda activate lexicon-mpx1-sysex-tests-env

To initialize it (venv):

    virtualenv -p $(command -v python3) larc-venv
    source larc-venv/bin/activate
    python3 -m pip install -r requirements.txt

To not depend on jack, the scripts use the `pygame` mido backend.

Under Ubuntu, this was necessary:

    yes | sudo apt install libasound2-plugins
    cd /usr/lib/x86_64-linux-gnu/
    sudo ln -s alsa-lib/libasound_module_conf_pulse.so libasound_module_conf_pulse.so
    cd -

Same thing on Raspberry Pi Zero:

    yes | sudo apt install libasound2-plugins libportmidi-dev libsdl2-dev
    cd /usr/lib/arm-linux-gnueabihf/
    sudo ln -s alsa-lib/libasound_module_conf_pulse.so libasound_module_conf_pulse.so
    cd -



## References

This was mostly using the [official MPX1 MIDI implementation reference](https://lexiconpro.com/en/product_documents/mpx1_v1_1_midi_impl_rev1pdf), with some bits guessed from the [official user guide](https://lexiconpro.com/en/product_documents/mpx1_user_guide_rev2pdf).

MIDI exchanges are implemented with [mido](https://mido.readthedocs.io/en/latest), notably the handling of [SysEx messages](https://mido.readthedocs.io/en/latest/messages.html#system-exclusive-messages).


## Similar projects

[jbeuckm/Ctrlr-Lexicon-MPX100](https://github.com/jbeuckm/Ctrlr-Lexicon-MPX100) ([making of video](https://www.youtube.com/watch?v=lszMkl3Jp1k&t=1218s)) is a panel for the [Ctrlr](https://ctrlr.org/) software control interface.
