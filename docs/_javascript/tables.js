// From: https://squidfunk.github.io/mkdocs-material/reference/data-tables/
document$.subscribe(function () {
  var tables = document.querySelectorAll("article table");
  tables.forEach(function (table) {
    new Tablesort(table);
  });
});
