# bash-preexec should be installed first
# https://github.com/rcaloras/bash-preexec

PROMPT="assistant"
HISTORY_FILE="$HOME/.assistant_history"

if [ -z "$_OLD_PROMPT" ]; then
    _OLD_PROMPT="$PS1"
fi

if [ -z "$_OLD_PREEXEC" ]; then
    if [ ! -z "$preexec" ]; then
        eval "$(echo "_OLD_PREEXEC()"; declare -f preexec | tail -n +2)"
    fi
fi

if [ -z "$TERM_ASSISTANT_ENABLED" ]; then
    export PS1="($PROMPT) $_OLD_PROMPT"
    echo > $HISTORY_FILE
    preexec() {
        echo "$1" >> $HISTORY_FILE
        if [ ! -z "$_OLD_PREEXEC" ]; then
            _OLD_PREEXEC "$1"
        fi
    }
    export TERM_ASSISTANT_ENABLED=1
else
    export PS1="$_OLD_PROMPT"
    if [ ! -z "$_OLD_PREEXEC" ]; then
        preexec() {
            _OLD_PREEXEC "$1"
        }
    fi
    unset TERM_ASSISTANT_ENABLED
fi
