---
description: Create a Tool
---

Write a tool that does what I describe and use the following context to guide the design of the tool.

## Tool Context
Built-in tools are installed by importing them directly in mcp-server/toolManager.ts and adding them to `defaultToolDefs`
Keep in mind that a tool runs IN THE BROWSER or a webview. It does NOT have access to node or any node related tools. They are primarily executed in the tauri app. If you need to know the API's available to any tauri tool that's installed, look them up using context7 or check out the official plugins page here (navigate to the plugin you need to check out): https://github.com/tauri-apps/plugins-workspace?tab=readme-ov-file#official-tauri-plugins

## Guidelines

* Add tools to the mcp-tools directory.
* Make tool functions short and to the point.
* Don't create too many tools.
* An easily callable API is essential to make calling them quick and easy.

## Tool Code Examples:

For tool examples check the mcp-tools directory. Here is a snippet:
```
import { makeToolSchema } from '@/lib/zod-tools';
import { z } from 'zod';

const addInputSchema = z.object({
   a: z.number().describe('First number to add'),
   b: z.number().describe('Second number to add'),
});

const addOutputSchema = z.object({ result: z.number() });

const addLogic = ({ a, b }: z.infer<typeof addInputSchema>): z.infer<typeof addOutputSchema> => {
   return { result: a + b };
};

export const add = makeToolSchema(
   'add',
   'Add two numbers together',
   addInputSchema,
   addOutputSchema,
   addLogic
);
```

Another example:
```
import { openUrl } from '@tauri-apps/plugin-opener';
import { z } from 'zod';
import { makeToolSchema } from '@/lib/zod-tools';

const zOpenUrl = z.object({
   url: z.string().url().describe('The URL to open.'),
   app: z.string().optional().describe('Optional application to use (e.g., "firefox").'),
});

const openUrlTool = makeToolSchema(
   'openUrl',
   'Open a URL in the default browser or a specified app.',
   zOpenUrl,
   undefined,
   async ({ url, app }: z.infer<typeof zOpenUrl>): Promise<void> => {
      await openUrl(url, app);
   }
);

export { openUrlTool }
```