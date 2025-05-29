set PROMPT "assistant"
set HISTORY_FILE "$HOME/.assistant_history"

if not functions -q _old_prompt
    functions -c fish_prompt _old_prompt
end

if not functions -q _old_preexec
    functions -c preexec _old_preexec
end

if not set -q TERM_ASSISTANT_ENABLED
    echo > $HISTORY_FILE

    function fish_prompt
        printf '(%s) ' $PROMPT
        _old_prompt
    end

    function preexec --on-event fish_preexec
        echo $argv[1] >> $HISTORY_FILE
    end

    set -gx TERM_ASSISTANT_ENABLED 1
else
    functions -e fish_prompt
    functions -c _old_prompt fish_prompt
    functions -e preexec
    functions -c _old_preexec preexec
    set -e TERM_ASSISTANT_ENABLED
end
