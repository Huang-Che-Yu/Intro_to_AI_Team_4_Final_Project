# This script is used to record the terminal session of the assistant

if ! command -v asciinema &> /dev/null
then
    echo "asciinema could not be found, please install asciinema before running this script."
    exit 1
fi

if [ "$(asciinema --version | grep -oP '\d+\.\d+\.\d+' | sort -V | head -n1)" != "3.0.0" ]; then
    echo "asciinema version is less than 3.0.0, please update asciinema."
    exit 1
fi

if [ "$1" == "rec" ] || [ -z "$1" ]; then
    echo -e "\e[32mRecording terminal session...\e[0m"
    asciinema rec -q -a "$HOME/.assistant.cast"
    echo -e "\e[32mRecording ended.\e[0m"
elif [ "$1" == "rotate" ]; then
    echo "Rotate subcommand is not implemented yet."
else
    echo "Invalid subcommand. Use 'rec' or 'rotate'."
    exit 1
fi
