_PROMPT="assistant"
HISTORY_FILE="$HOME/.assistant_history"

if [[ -z $_old_prompt ]]; then
    _old_prompt="$PROMPT"
fi

if [[ -z $(whence -w _old_preexec) ]]; then
    functions[_old_preexec]=$functions[preexec]
fi

if [[ -z $TERM_ASSISTANT_ENABLED ]]; then
    echo > $HISTORY_FILE

    export PROMPT="($_PROMPT) $_old_prompt"

    function preexec {
        echo $1 >> $HISTORY_FILE
        if [[ -n ${functions[_old_preexec]+x} ]]; then
            _old_preexec $1
        fi
    }

    export TERM_ASSISTANT_ENABLED=1
else
    export PROMPT=$_old_prompt
    unfunction preexec
    functions[preexec]=$_old_preexec
    unset TERM_ASSISTANT_ENABLED
fi
