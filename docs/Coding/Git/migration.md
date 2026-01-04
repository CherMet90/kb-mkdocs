1. Проверяем какие существуют удаленные репозитории:  
```
   git remote -v
```  
2. Если есть удаляем ненужные по имени. Например:  
```
   git remote remove github
   git remote remove origin
```  
3. Добавляем новый удаленный репо:  
```
   git remote add origin https://git.example.com/username/reponame.git
   git push origin --all
   git push origin --tags
```