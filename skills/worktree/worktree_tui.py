#!/usr/bin/env python3
"""Textual TUI for the worktree manager."""

import subprocess

from rich.text import Text

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, Label, ListItem, ListView, Static


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
      ("c", "cd", "cd"),
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
      self.action_cd()

   def action_cd(self):
      """Exit the TUI with the selected worktree path so the shell can cd."""
      entry = self._selected_entry()
      if entry:
         self.exit(2, entry['worktree_path'])

   def action_open_editor(self):
      """Open the highlighted worktree in the configured editor."""
      entry = self._selected_entry()
      if entry:
         subprocess.Popen(
            [entry['editor'], entry['worktree_path']],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
         )

   def action_open_diff(self):
      """Open the highlighted worktree in the configured diff tool."""
      entry = self._selected_entry()
      if entry:
         subprocess.Popen(
            [entry['diff'], entry['worktree_path']],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
         )

   def action_refresh(self):
      """Re-scan worktrees and re-render the list."""
      self.exit(1, 1)

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
      details.update(self._render_details(entry))

   def _render_details(self, entry):
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
