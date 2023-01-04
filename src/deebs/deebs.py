from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.reactive import var
from textual.widgets import Tree, Footer, Header, Static
from textual.widgets import DataTable
from textual import log

import sqlalchemy
from sqlalchemy import create_engine, Engine
from sqlalchemy.schema import MetaData


class DatabaseTree(Tree[dict]):
    """Database tree widget (shows overall database structure)"""

    def __init__(self, db_engine: Engine, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.engine = db_engine
        self.metadata_obj = MetaData()
        self.metadata_obj.reflect(bind=self.engine)

        self.root.expand()
        self.tables_node = self.root.add("Tables", expand=True)
        self.tables_dict = self.metadata_obj.tables

        self.selected_node = None

        for table_name, table in self.tables_dict.items():
            log(table_name=table_name, table=table)
            self.tables_node.add_leaf(table_name, data=table)

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Called when the user clicks an entry in the database tree."""
        if self.selected_node is not None:
            self.selected_node.set_label(self.selected_node.data.description)
            self.refresh()

        self.selected_node = None
        node = event.node
        log(f'node selected: {node}')
        log(f'data for selected node: {node.data}')

        if isinstance(node.data, sqlalchemy.sql.schema.Table):
            # Not super happy with this at the moment. Will style the TreeNode via CSS when it's supported.
            log('Table item selected')
            self.selected_node = node
            node.set_label(f'[bold red]{node.data.description}[/]')


class DatabaseBrowser(App):
    """Textual database browser app."""

    CSS_PATH = "deebs.css"
    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    selected_node = None
    show_tree = var(True)

    engine = create_engine(f'sqlite:///sample databases/chinook.db')

    def compose(self) -> ComposeResult:
        """Compose our UI."""

        tree = DatabaseTree(self.engine, 'Database', id='tree-view')

        yield Container(
            tree,
            Vertical(DataTable(id='datatable'), id='data-view'),
        )
        yield Header()
        yield Footer()

    def on_mount(self, event: events.Mount) -> None:
        self.query_one(DatabaseTree).focus()

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Called when the user clicks an entry in the database tree."""
        event.stop()

        node = event.node

        if isinstance(node.data, sqlalchemy.sql.schema.Table):
            log('Table item selected')
            dbtable = node.data

            datatable: DataTable = self.query_one('#datatable')
            datatable.clear(columns=True)
            datatable.add_columns(*[col.name for col in dbtable.columns])

            with self.engine.connect() as conn:
                for row in conn.execute(dbtable.select().limit(100)):
                    datatable.add_row(*map(str, row))


# Entry point for script when installed via pip/pipx
def main():
    DatabaseBrowser().run()


if __name__ == "__main__":
    main()
