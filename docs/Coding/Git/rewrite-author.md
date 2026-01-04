Скрипт для переписывания истории авторов в Git (например, после смены e-mail).

### Пример скрипта (Bash):

```bash
git filter-branch --env-filter '
OLD_EMAIL="old@example.com"
CORRECT_NAME="New Name"
CORRECT_EMAIL="new@example.com"
if [ "$GIT_COMMITTER_EMAIL" = "$OLD_EMAIL" ]
then
    export GIT_COMMITTER_NAME="$CORRECT_NAME"
    export GIT_COMMITTER_EMAIL="$CORRECT_EMAIL"
fi
if [ "$GIT_AUTHOR_EMAIL" = "$OLD_EMAIL" ]
then
    export GIT_AUTHOR_NAME="$CORRECT_NAME"
    export GIT_AUTHOR_EMAIL="$CORRECT_EMAIL"
fi
' --tag-name-filter cat -- --all
```

⚠️ После этого нужно перезаписать историю на удалённом репозитории:

```bash
git push --force origin --all
git push --force origin --tags
```

🔒 Внимание: эта операция переписывает историю и потенциально ломает ссылки, используйте только если работаете в одиночку или вся команда согласована.
