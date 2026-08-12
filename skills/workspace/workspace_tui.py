#!/usr/bin/env python3
"""Textual TUI for the workspace manager: projects grid and project window."""

import os
import subprocess

from rich.text import Text

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Container, Grid, Horizontal, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import Header, Footer, Input, Label, ListItem, ListView, Static

import workspace


class WorktreeListItem(ListItem):
   """A single row in the interactive worktree list."""

   DEFAULT_CSS = """
   WorktreeListItem > Horizontal {
      height: 1;
      width: 100%;
   }
   WorktreeListItem .col {
      height: 1;
      content-align: left middle;
   }
   WorktreeListItem .ago {
      width: 14;
   }
   WorktreeListItem .branch {
      width: 24;
   }
   WorktreeListItem .repo {
      width: 18;
   }
   WorktreeListItem .path {
      width: 1fr;
   }
   """

   def __init__(self, entry, **kwargs):
      """
      @param dict entry - worktree data with repo, branch, path, ago, editor
      """
      super().__init__(**kwargs)
      self.entry = entry

   def compose(self) -> ComposeResult:
      with Horizontal(classes='row'):
         yield Label(self.entry['ago'], classes='col ago')
         yield Label(self.entry['branch'], classes='col branch')
         yield Label(self.entry['name'], classes='col repo')
         yield Label(self.entry['display_path'], classes='col path')


class WorktreeListApp(App):
   """Interactive list of worktrees sorted by recent activity."""

   CSS = """
   Screen { align: center middle; }
   #main { width: 100%; height: 100%; }
   #worktree-list {
      width: 100%;
      height: 1fr;
      border: solid green;
   }
   #details {
      width: 100%;
      height: auto;
      min-height: 3;
      border: solid blue;
      padding: 0 1;
   }
   """

   BINDINGS = [
      ("q", "quit", "Quit"),
      ("r", "refresh", "Refresh"),
      ("o", "open_editor", "Open"),
      ("d", "open_diff", "Diff"),
      ("c", "claude", "claude"),
      ("enter", "cd", "cd"),
   ]

   def __init__(self, worktrees, **kwargs):
      """
      @param list[dict] worktrees - sorted worktree entries with display keys
      """
      super().__init__(**kwargs)
      self.worktrees = worktrees

   def compose(self) -> ComposeResult:
      yield Header(show_clock=True)
      with Container(id='main'):
         items = [WorktreeListItem(wt) for wt in self.worktrees]
         yield ListView(*items, id='worktree-list')
         yield Static("Select a worktree to see details.", id='details')
      yield Footer()

   def on_list_view_highlighted(self, event):
      """Update the detail panel when the highlighted row changes."""
      item = event.item
      if not item or not hasattr(item, 'entry'):
         self._show_details(None)
         return
      self._show_details(item.entry)

   def on_list_view_selected(self, event):
      """Default action: cd into the selected worktree."""
      item = event.item
      if not hasattr(item, 'entry'):
         return
      self._cd_to_entry(item.entry)

   def action_cd(self):
      """Exit the TUI with a cd command for the selected worktree."""
      entry = self._selected_entry()
      if entry:
         self._cd_to_entry(entry)

   def action_claude(self):
      """Exit the TUI with a cd command that also starts claude."""
      entry = self._selected_entry()
      if entry:
         self._cd_to_entry(entry, run_claude=True)

   def _cd_to_entry(self, entry, run_claude=False):
      """@param dict entry - exit with a shell command for worktree_path."""
      self.exit(workspace.cd_command(entry['worktree_path'], run_claude))

   def action_open_editor(self):
      """Open the highlighted worktree in the configured editor."""
      entry = self._selected_entry()
      if entry:
         _launch(entry['editor'], entry['worktree_path'])

   def action_open_diff(self):
      """Open the highlighted worktree in the configured diff tool."""
      entry = self._selected_entry()
      if entry:
         _launch(entry['diff'], entry['worktree_path'])

   def action_refresh(self):
      """Re-scan worktrees and re-render the list."""
      self.exit(1, return_code=1)

   def _selected_entry(self):
      """@return dict|None - entry for the currently highlighted row."""
      list_view = self.query_one('#worktree-list', ListView)
      if list_view.index is None:
         return None
      item = list_view.children[list_view.index]
      if not hasattr(item, 'entry'):
         return None
      return item.entry

   def _show_details(self, entry):
      """Render metadata for the selected worktree in the detail panel."""
      details = self.query_one('#details', Static)
      if not entry:
         details.update("")
         return
      details.update(render_details(entry))


def _launch(command, path):
   """
   Start a GUI tool detached from the TUI.

   @param str command - executable name
   @param str path - directory to open
   """
   subprocess.Popen(
      [command, path],
      start_new_session=True,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
   )


def render_details(entry):
   """
   @param dict entry - worktree entry with metadata
   @return Text|str - rendered details with clickable links
   """
   metadata = entry.get('metadata', {})
   if not metadata:
      return "No metadata"

   title = metadata.get('title', '')
   notes = metadata.get('notes', '')
   tickets = metadata.get('tickets', [])
   links = metadata.get('links', [])

   parts = []
   if title:
      parts.append(Text(f"Title: {title}", style='bold'))
   if notes:
      parts.append(Text(f"Notes: {notes}"))
   if tickets:
      ticket_text = Text('Tickets: ')
      for i, ticket in enumerate(tickets):
         if i > 0:
            ticket_text.append('  ')
         ticket_text.append(ticket, style=f"link {ticket}")
      parts.append(ticket_text)
   if links:
      link_text = Text('Links: ')
      for i, link in enumerate(links):
         if i > 0:
            link_text.append('  ')
         if isinstance(link, dict):
            label = link.get('label') or link.get('url', '')
            url = link.get('url', '')
         else:
            label = str(link)
            url = str(link)
         link_text.append(label, style=f"link {url}")
      parts.append(link_text)

   if not parts:
      return "No metadata"

   return Text("\n").join(parts)


class ProjectBox(Static):
   """A focusable box in the projects grid representing one configured repo."""

   can_focus = True

   def __init__(self, project, **kwargs):
      """
      @param dict project - project entry with name, count, ago
      """
      super().__init__(**kwargs)
      self.project = project

   def render(self):
      count = self.project['count']
      label = 'workspace' if count == 1 else 'workspaces'
      return Text.assemble(
         (f"{self.project['name']}\n", 'bold'),
         f"{count} {label}\n",
         (self.project['ago'], 'dim'),
      )


class ProjectsScreen(Screen):
   """Grid of configured projects — the default entry point."""

   CSS = """
   #projects {
      grid-size: 4;
      grid-gutter: 1;
      grid-rows: 5;
      padding: 1;
   }
   ProjectBox {
      border: solid grey;
      padding: 0 1;
      height: 5;
   }
   ProjectBox:focus {
      border: solid green;
   }
   """

   BINDINGS = [
      ("q", "quit", "Quit"),
      ("r", "refresh", "Refresh"),
      ("enter", "select", "Open project"),
      ("right", "focus_next", "Next"),
      ("down", "focus_next", "Next"),
      ("left", "focus_previous", "Previous"),
      ("up", "focus_previous", "Previous"),
   ]

   def compose(self) -> ComposeResult:
      yield Header(show_clock=True)
      with Grid(id='projects'):
         for project in self.app.projects:
            yield ProjectBox(project)
      yield Footer()

   def on_mount(self):
      boxes = self.query(ProjectBox)
      if boxes:
         boxes.first().focus()

   def action_select(self):
      """Open the project window for the focused project."""
      box = self.focused
      if isinstance(box, ProjectBox):
         self.app.push_screen(ProjectScreen(box.project))

   def on_click(self, event):
      """Open a project when its box is clicked."""
      widget = event.widget
      if isinstance(widget, ProjectBox):
         self.app.push_screen(ProjectScreen(widget.project))

   def action_refresh(self):
      """Re-scan projects and rebuild the grid."""
      self.app.reload_projects()
      self.refresh(recompose=True)


class ProjectRow(ListItem):
   """A single row in a project window: the mainline repo or a workspace."""

   DEFAULT_CSS = """
   ProjectRow > Horizontal {
      height: 1;
      width: 100%;
   }
   ProjectRow .col {
      height: 1;
      content-align: left middle;
   }
   ProjectRow .ago {
      width: 14;
   }
   ProjectRow .branch {
      width: 30;
   }
   ProjectRow .path {
      width: 1fr;
   }
   """

   def __init__(self, entry, **kwargs):
      """
      @param dict entry - row data with branch, ago, display_path, status
      """
      super().__init__(**kwargs)
      self.entry = entry

   def compose(self) -> ComposeResult:
      is_mainline = self.entry.get('mainline', False)
      branch = self.entry['branch']
      label = f"{branch} (mainline)" if is_mainline else branch
      detail = self.entry.get('status', '') if is_mainline else self.entry['display_path']
      with Horizontal():
         yield Label(self.entry['ago'], classes='col ago')
         yield Label(label, classes='col branch')
         yield Label(detail, classes='col path', id='row-detail')


class ProjectScreen(Screen):
   """Workspaces for a single project, newest first, with a mainline row."""

   CSS = """
   #rows {
      width: 100%;
      height: 1fr;
      border: solid green;
   }
   #details {
      width: 100%;
      height: auto;
      min-height: 3;
      border: solid blue;
      padding: 0 1;
   }
   """

   BINDINGS = [
      ("escape", "back", "Back"),
      ("q", "back", "Back"),
      ("enter", "cd", "cd"),
      ("o", "open_editor", "Open"),
      ("d", "open_diff", "Diff"),
      ("c", "claude", "claude"),
      ("n", "new_workspace", "New"),
      ("r", "refresh", "Refresh"),
   ]

   def __init__(self, project, **kwargs):
      """
      @param dict project - project entry from the grid
      """
      super().__init__(**kwargs)
      self.project = project
      self.rows = []

   def compose(self) -> ComposeResult:
      yield Header(show_clock=True)
      self.rows = workspace.build_project_worktrees(
         self.app.config, self.project['name']
      )
      with Vertical():
         yield ListView(*[ProjectRow(row) for row in self.rows], id='rows')
         yield Static(f"Project: {self.project['name']}", id='details')
      yield Footer()

   def on_mount(self):
      self.sub_title = self.project['name']
      self.sync_mainline()

   @work(thread=True)
   def sync_mainline(self):
      """Fetch and fast-forward the canonical repo without blocking the UI."""
      status = workspace.sync_mainline(self.project['repo_path'])
      self.app.call_from_thread(self._set_mainline_status, status)

   def _set_mainline_status(self, status):
      """
      @param str status - message describing the mainline sync result
      """
      if not self.rows:
         return
      self.rows[0]['status'] = status
      list_view = self.query_one('#rows', ListView)
      first = list_view.children[0] if list_view.children else None
      if first:
         first.query_one('#row-detail', Label).update(status)

   def action_back(self):
      """Return to the projects grid."""
      self.app.pop_screen()

   def action_refresh(self):
      """Rebuild the rows for this project."""
      self.refresh(recompose=True)
      self.sync_mainline()

   def action_cd(self):
      entry = self._selected_entry()
      if entry:
         self.app.exit_with_command(
            workspace.cd_command(entry['worktree_path'])
         )

   def action_claude(self):
      entry = self._selected_entry()
      if entry:
         self.app.exit_with_command(
            workspace.cd_command(entry['worktree_path'], run_claude=True)
         )

   def on_list_view_selected(self, event):
      """Default action: cd into the selected row."""
      if hasattr(event.item, 'entry'):
         self.app.exit_with_command(
            workspace.cd_command(event.item.entry['worktree_path'])
         )

   def on_list_view_highlighted(self, event):
      """Show metadata for the highlighted row."""
      details = self.query_one('#details', Static)
      item = event.item
      if not item or not hasattr(item, 'entry'):
         details.update('')
         return
      details.update(render_details(item.entry))

   def action_open_editor(self):
      entry = self._selected_entry()
      if entry:
         _launch(entry['editor'], entry['worktree_path'])

   def action_open_diff(self):
      entry = self._selected_entry()
      if entry:
         _launch(entry['diff'], entry['worktree_path'])

   def action_new_workspace(self):
      """Prompt for a branch, base ref, and optional workspace name."""
      self.app.push_screen(NewWorkspaceScreen(self.project))

   def _selected_entry(self):
      """@return dict|None - entry for the currently highlighted row."""
      list_view = self.query_one('#rows', ListView)
      if list_view.index is None:
         return None
      item = list_view.children[list_view.index]
      if not hasattr(item, 'entry'):
         return None
      return item.entry


class NewWorkspaceScreen(ModalScreen):
   """Prompt for the details of a new workspace."""

   CSS = """
   NewWorkspaceScreen {
      align: center middle;
   }
   #form {
      width: 70;
      height: auto;
      border: solid green;
      padding: 1 2;
      background: $surface;
   }
   #form Label {
      margin-top: 1;
   }
   #error {
      color: red;
   }
   """

   BINDINGS = [
      ("escape", "cancel", "Cancel"),
   ]

   def __init__(self, project, **kwargs):
      """
      @param dict project - project the workspace belongs to
      """
      super().__init__(**kwargs)
      self.project = project

   def compose(self) -> ComposeResult:
      base = workspace.default_branch(
         self.project['repo_path'], self.app.config, self.project['name']
      ) or ''
      with Vertical(id='form'):
         yield Static(f"New workspace in {self.project['name']}", classes='title')
         yield Label('Branch name')
         yield Input(placeholder='feature/my-change', id='branch')
         yield Label('Base ref')
         yield Input(value=base, id='base-ref')
         yield Label('Workspace name (optional)')
         yield Input(placeholder='defaults to branch name', id='dir-name')
         yield Static('', id='error')

   def on_mount(self):
      self.query_one('#branch', Input).focus()

   def action_cancel(self):
      """Close the prompt without creating anything."""
      self.app.pop_screen()

   def on_input_submitted(self, event):
      """Create the workspace once the form has a branch name."""
      branch = self.query_one('#branch', Input).value.strip()
      if not branch:
         self.query_one('#error', Static).update('Branch name is required')
         return

      base_ref = self.query_one('#base-ref', Input).value.strip()
      dir_name = self.query_one('#dir-name', Input).value.strip()

      try:
         path = workspace.create_workspace(
            self.app.config, self.project['name'], branch, base_ref,
            dir_name, self.app.launch_cwd,
         )
      except SystemExit as e:
         self.query_one('#error', Static).update(str(e) or 'Could not create workspace')
         return

      self.app.exit_with_command(workspace.cd_command(path))


class WorkspaceApp(App):
   """Projects grid plus per-project windows."""

   TITLE = 'workspace'

   def __init__(self, config, config_path, **kwargs):
      """
      @param dict config - parsed config
      @param str config_path - path to the config file
      """
      super().__init__(**kwargs)
      self.config = config
      self.config_path = config_path
      self.launch_cwd = os.getcwd()
      self.projects = workspace.build_projects(config)

   def on_mount(self):
      self.push_screen(ProjectsScreen())

   def reload_projects(self):
      """Re-scan configured repos for the grid."""
      self.projects = workspace.build_projects(self.config)

   def exit_with_command(self, command):
      """
      Hand a shell command to the wrapper and quit.

      @param str command - shell command, e.g. "cd '/path'"
      """
      workspace.write_shell_command(command)
      self.exit()
