## Building containers
First, make sure you have Docker installed.

### SignalP
1. Go to this website and fill in the form to get access to SignalP
2. Download the code
3. Put the code in the same folder as the SignalP Dockerfile (see folder `signalp`)
4. Run the `build.sh` script
5. Test the container with the `test.sh` script

### TMHMM
1. Go to this website and fill in the form to get access to TMHMM
2. Download the code
3. Put the code in the same folder as the TMHMM Dockerfile (see folder `tmhmm`)
4. Run the `build.sh` script
5. Test the container with the `test.sh` script
6. Move the `TMHMM2.0.model` file to the assets folder of the workflow

Now make sure to replace the container paths of these modules (`modules/local/signalp/signalp.nf` and `modules/local/tmhmm/tmhmm.nf`). If you use Singularity (on an HPC for example, without sudo access), the Docker containers will automatically be translated into Singularity containers.