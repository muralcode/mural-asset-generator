# mural-asset-generator
======
## Financial App
This is the script that generates the needed assets for iOS and in future android from the asset
bundles given by clients in JSON format, using Python (3.7 syntax).

The asset generator is wrapped in a docker container to simplify cross-platform operation.
The goal is to make the financial app distributable among clients and different plartforms (ios/android).

Setup
-------
Install docker and check out the guides [here][1] and [here][2]

There might be minor syntactical differences between docker execution on Windows and
Unix/Linux plaforms, but the docker image always works the same way.

Execution
--------
When required to run the docker image locally (Android studio does this for you),
it can be handled as follows:

The below line deletes, rebuilds, and executes the docker image with certain paths pre-mounted.

```docker rmi assetgeneratornextgen37 ; ./start.sh -p=all -c=edt -lf=1 -l=/path/to/app-white-labelling```

Revision Control
--------
See the [Changelog][2]

Source can be found in [Github][2]

 [1]: https://www.docker.com/
 [2]: https://github.com/muralcode/mural-asset-generator/edit/master/CHANGELOG.md
