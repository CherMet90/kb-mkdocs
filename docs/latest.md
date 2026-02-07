---
render_macros: true
---

# Последние обновления

{% for post in latest_posts(10) %}
<article>
  <h2><a href="{{ post.url }}">{{ post.title }}</a></h2>
  <p><small>Дата последнего обновления: {{ post.date.strftime("%Y-%m-%d") }}</small></p>
  <p>
  {{ post.excerpt }}
  </p>
  <p><a href="{{ post.url }}">Читать далее...</a></p>
</article>
<hr>
{% endfor %}