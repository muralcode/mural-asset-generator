#!/bin/bash

#################################
# Author/Engineer: Lerato Mokoena
# Set constants #
#
#################################

# Parameter identifiers used to validate input parameters
CL="-c"
CL_LONG="--client"
LOC="-l"
LOC_LONG="--location"
LF="-lf"
LF_LONG="--localfolder"
TG="-t"
TG_LONG="--targets"
PF="-p"
PF_LONG="--platform"
AB="-b"
AB_LONG="--android_branch"
IB="-i"
IB_LONG="--ios_branch"
IP="ip"
IP_LONG="--ios_project"
AP="ip"
AP_LONG="--android_project" #future implementation

# Docker image name
DOCKER_BASE=assetgeneratorbase37
DOCKER_IMAGE=assetgeneratornextgen37

####################
# Define functions #
####################

# Echo a open line. This has been put into a function to increase code readability.
echo_spacer(){
	echo ""
}

echo_error(){
	echo -e "[ERROR]\t$1"
}

echo_info(){
	echo -e "[INFO]\t$1"
}

clean_folder(){
	if [ -z "$reponame" ]; then
		echo_info "Cannot clean folder, parameter $reponame was empty."
	else
		echo_info "Cleaning temporary files and folders."
		rm -rf "$reponame"
		rm -rf "$targetname"
	fi
}

fatal_error(){

	echo_error "$1"
	echo_info "Stopping safely."
	# Clean folder run by trap set at start of script
	exit 1
}

# $1=Source type $2=Source location
validate_asset_source(){

	echo_info "Validating asset parameters."

	# Validate source type
	if [ $1 -ne 0 ] && [ $1 -ne 1 ]; then
		fatal_error "Local folder ($LF) not 0 or 1"
	fi

	# Validate source location
	if [ $1 -eq 1 ] && [ "$(ls -A "$2" 2>/dev/null | wc -l)" -eq 0 ]; then
		fatal_error "Local folder $2 doesn't exist or is empty."
	fi

	echo_info "Asset parameters valid."
}

# $1=Source location
validate_targets_source() {

	echo_info "Validating targets parameter."

	# Validate source location
	if [ "$(ls -A "$1" 2>/dev/null | wc -l)" -eq 0 ]; then
		fatal_error "Local folder $1 doesn't exist or is empty."
	fi

	echo_info "Targets parameters valid."
}

# $1=path
validate_asset_source_contents() {

	echo_info "Validating asset source content."

	files_count="$(ls -A "$1/$reponame/" 2>/dev/null | wc -l)"
	if [ $files_count -eq 0 ]; then
		fatal_error "Folder for $client not found inside asset data folder."
	else
		files_count_json="$(ls -A "$1/$reponame/data.json" 2>/dev/null | wc -l)"
		if [ $files_count_json -eq 0 ]; then
			fatal_error "Folder for $client doesn't contain a data.json file."
		fi
	fi

	echo_info "Asset source content valid at surface glance."
}

####################
# Main script code #
####################

# Set defaults
client='all'
asset_source_location='github.com/muralcode/app-white-labelling.git'
source_is_local=0
reponame='client'
targetname='targets'
targets_location='../app-white-labelling' #This will house all the data and CICD for fetching apple certificates and prov profiles
platform='all'
ANDROID_BRANCH='master'
IOS_BRANCH='master'
IOS_PROJECT="../FinancialApp-ios"
ANDROID_PROJECT="../FinancialApp-android" # Future implementation
# Set traps for various signals
trap "clean_folder" EXIT
trap "echo_spacer; fatal_error 'Something went wrong. See the output above for information.'" ERR

# Extract input parameters
echo_spacer
echo_info "Parsing input parameters."

for i in "$@"
do
	case "$i" in
		$CL=* | $CL_LONG=*)
			client="${i#*=}"
			;;
		$LOC=* | $LOC_LONG=*)
			asset_source_location="${i#*=}"
			;;
	  $TG=* | $TG_LONG=*)
			targets_location="${i#*=}"
			;;
		$LF=* | $LF_LONG=*)
			source_is_local="${i#*=}"
			;;
		$PF=* | $PF_LONG=*)
			platform="${i#*=}"
			;;
		$AB=* | $AB_LONG=*)
			ANDROID_BRANCH="${i#*=}"
			;;
		$IB=* | $IB_LONG=*)
			IOS_BRANCH="${i#*=}"
			;;
		$IP=* | $IP_LONG=*)
			IOS_PROJECT="${i#*=}"
			;;
	  $AP=* | $AP_LONG=*)
			ANDROID_PROJECT="${i#*=}"
			;;

		-h | --help)
			echo ""
			echo "usage: ./start.sh [$CL=<client name> | $CL_LONG=<client name>]"
			echo "                  [$LOC=<assets location> | $LOC_LONG=<assets location>]"
			echo "                  [$LF=<0 or 1> | $LF_LONG=<0 or 1>]"
			echo "                  [$CT=<temp folder name> | $CT_LONG=<temp folder name>]"
			echo ""
			echo "Example: "
			echo "./start.sh $CL=Nedbank $LF=1 $LOC=/var/lib/tools/workspace/build/asset-input"
			echo ""
			trap "" EXIT
			exit 0
			;;
		*)
			fatal_error "Unrecognized command ${i}"
			;;
	esac
done

validate_asset_source "$source_is_local" "$asset_source_location"
validate_targets_source "$targets_location"

# Print some common input variables for quick debugging
if [ "$client" == "all" ]; then
	echo_info "Building all clients."
else
	echo_info "Building client = $client"
fi
echo_info "Client data location = $asset_source_location"
echo_info "Client targets location = $targets_location"

# Clone git repo if not using local repo
path=`pwd`

if [ "$source_is_local" -ne 1 ]; then
	echo_info "Cloning client data from git repository."
	echo_spacer
	git clone "$asset_source_location" "$reponame"
	echo_spacer
else
	echo_info "Using client data from local folder."
	cp -a "$asset_source_location/." "$reponame/"
fi

cp -a "$targets_location/." "$targetname/"

# Validation doesn't work for the 'all' shorthand
if [ $client != "all" ]; then
	validate_asset_source_contents $path
fi

# Launch docker image
image_base=$DOCKER_BASE:latest
image_name=$DOCKER_IMAGE:latest

if [ -z "$(docker images -q $image_name 2>/dev/null)" ]; then
	echo_info "Missing docker image $DOCKER_IMAGE. Building a new one."
	echo_spacer
  if [ -z "$(docker images -q $image_base 2>/dev/null)" ]; then
  	echo_info "Missing docker base image $DOCKER_BASE. Building a new one."
  	echo_spacer
  	docker build ./ -t $DOCKER_BASE -f Dockerfile.base
  	echo_spacer
  fi
	docker build ./ -t $DOCKER_IMAGE
	echo_spacer
fi

echo_info "Running docker image."
echo_spacer

docker run --rm \
	-e CLIENT_KEY=${client} \
	-e PLATFORM=${platform} \
	-e BUILD=${BUILD} \
	-e ANDROID_BRANCH=${ANDROID_BRANCH} \
	-e IOS_BRANCH=${IOS_BRANCH} \
	-v $path/$reponame:/usr/src/app/$reponame \
	-v $path/output:/usr/src/app/output \
	-v $path/input:/usr/src/app/input \
	-v $path/$targetname:/usr/src/app/$targetname \
	-v $path/${IOS_PROJECT}/Financial:/usr/src/app/Financial \
	-v $path/${IOS_PROJECT}:/usr/src/FinancialApp-ios \
	#-v $path/${ANDROID_PROJECT}:/usr/src/FinancialApp-android \ future native android implementation
	$image_name python ./generate_app_assets.py -p /usr/src/app/
echo_spacer
echo_info "Succesfully generated assets. See $path/output for the generated assets."
