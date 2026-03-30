---
render_macros: true
---

# Последние обновления

{% for post in latest_posts(10) %}
<small>
  {{ post.date.strftime('%Y-%m-%d') }}
  {% if post.path %} | <i>{{ post.path }}</i>{% endif %}
</small>

{{ post.excerpt }}

[Читать далее...]({{ post.url }})

---
{% endfor %}