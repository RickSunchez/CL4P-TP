# Трепло

Простой бот для размножения сообщений

Алгоритм прост:

0. Не забываем прописать данные для TG и FB в файлы credentials.json и fb.json
1. запускаем бота:

```bash
python3 main.py
// ИЛИ

// собираем контейнер 
docker build -t chatbot .
// и запускаем 
docker run -d --restart=always --name=cl4p-tp chatbot
```

2. добавляем группы или каналы, важно:
    1. группа или канал должны быть публичными
    2. бот должен быть в администраторах
3. создаем пост
4. profit!


[Ссылка на бота](https://t.me/cl4p_tp_007_bot)

[Группа для теста 1](https://t.me/cl4p_tp_007_group)

[Группа для теста 2](https://t.me/cl4p_tp_007_group2)

[Канал для теста](https://t.me/cl4p_tp_007_chanel)
