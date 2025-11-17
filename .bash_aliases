# ~/.bash_aliases

# Показать структуру ClearyFi
alias clearyfi-tree='cd ~/projects/clearyfi && tree -I "backup_old_structure|__pycache__|*.pyc" -C'

# Быстрый переход в проект
alias cf='cd ~/projects/clearyfi'

# Запуск структуры через Python
alias show='cd ~/projects/clearyfi && python show_structure.py'

# Обновить структуру в README
alias update-clearyfi-structure='cd ~/projects/clearyfi && python update_structure.py'

alias cfshow='tree -I "__pycache__|*.pyc|*.pyo|*.pyd|.git|.vscode|.idea|venv|env|backup*|cache|temp|tmp" -P "*.py|*.txt|*.md|.env*" --dirsfirst -C'
