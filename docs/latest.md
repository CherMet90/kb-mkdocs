---
render_macros: true
---

# Последние обновления

{% for post in latest_posts(10) %}
<small>Дата последнего обновления: {{ post.date.strftime('%Y-%m-%d') }}</small>

{% if post.path %}
<nav aria-label="breadcrumb">
  <ol class="md-breadcrumbs">
    {% for crumb in post.path %}
    <li class="md-breadcrumbs__item">
      <a href="{{ crumb.url }}">{{ crumb.title }}</a>
    </li>
    {% endfor %}
    <li class="md-breadcrumbs__item">
      <span>{{ post.title }}</span>
    </li>
  </ol>
</nav>
{% endif %}

{{ post.excerpt }}

[Читать далее...]({{ post.url }})

---
{% endfor %}