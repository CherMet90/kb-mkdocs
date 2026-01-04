### Задать имя и e-mail:

- Глобально (на пользователя системы):

  ```bash
  git config --global user.name "Your Name"
  git config --global user.email "you@example.com"
  ```

- Локально (только для текущего репозитория):

  ```bash
  git config user.name "Project Name"
  git config user.email "project@example.com"
  ```

### Просмотр текущих значений:

```bash
git config --get user.name
git config --get user.email
```
