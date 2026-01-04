### Просмотр текущих удалённых:

```bash
git remote -v
```

### Добавление дополнительного удалённого репозитория:

```bash
git remote add backup https://git.example.com/user/repo.git
```

Можно давать любые имена (`origin`, `github`, `backup`, и т.д.) — имя будет участвовать в командах push/fetch/pull.

### Отправка изменений в конкретный удалённый репозиторий:

```bash
git push backup main
```

### Удаление удалённого репозитория:

```bash
git remote remove backup
```
