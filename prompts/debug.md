---
description: debug
auto_execution_mode: 1
---

Take a step back.

I'm getting this error. I will describe it and paste any relevant logs. Use the following principles to guide you:

1. Methodically analyze the code. 
2. Ask yourself questions like: What makes it tick? Do I fully understand the API's involved? What does the data likely look like during runtime?
3. Create a list of hypothosis' that describe the potential cause of the error.
4. Consider each individual hypothosis and follow the train of thought logically. Consider what assumptions those hypothosis are based on.
5. Gather more insight. If you need to investigate the situation at runtime, consider adding temporray log messages that begin with "[tmp]" to get more visibility.
6. Give the user a TLDR of the questions you are exploring and your hypothosis. (provide a BRIEF bulleted list each a sentence long with the hypothosis. Add an arrow to the one you suspect with an explanation under it).


IMPORTANT: be sure to remove all debug log messages you added with "[tmp]" once the the investigation is over. (Don't assume it's over. Wait for the user to tell you they are done.)