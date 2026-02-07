---
render_macros: true
---

# Последние обновления

{% for post in latest_posts(10) %}
<small>Дата последнего обновления: {{ post.date.strftime('%Y-%m-%d') }}</small>

{{ post.excerpt }}

[Читать далее...]({{ post.url }})

---
{% endfor %}
