---
description: Create Dynamo Table Workflow
auto_execution_mode: 1
---

# DynamoDB Query Analysis and Optimization

**Objective:**
Analyze how the specific DynamoDB table(s) specified are queried across a codebase,
document the query patterns in a concise markdown file to assist in querying the table in
general ways.

---

## Workflow Steps

### **Step 1: Understand table(s)**
- Find table definition in the codebase.
- List off GSIs, PKs, SKs, and any other relevant attributes.
- Read related documentation markdown files.
- Create a brief summary of the table and it's attributes, as well as what they are used for.

### **Step 2: Locate All Queries**
- Search the entire codebase for all instances where the target DynamoDB tables are queried.
- Include all relevant query types: `get`, `query`, `scan`, `batchGet`, etc.
- Capture the full TypeScript code snippets used to perform these queries.
- **IMPORTANT:** be extremely thorough when searching the codebase.

### **Step 3: Document Query Patterns**
- Create a markdown file in the **root directory** named something like `${tablename}-query-patterns.md`.
- For each table:
  - List all the ways it is queried.
  - Include the **exact TypeScript code** used for each query.
  - Be **concise** and **avoid fluff**—focus on clarity and completeness.
  - Use headings and code blocks to organize the content clearly and identify the purpose
    of a query. Eg: 'get user by email address', 'scan users by role', etc...

#### **Step 4: Analyze Query Efficiency**
- Review each query and determine if it is **potentially expensive** (e.g., full table scans, unindexed queries).
- Add a **warning** next to any expensive queries in the markdown file.
  - Example: `⚠️ This query may be expensive.`

#### **Step 5: Suggest Optimizations**
- For each expensive query:
  - Check if there is a **more efficient alternative** already used elsewhere in the codebase.
  - Prefer queries that:
    - Use indexes
    - Filter on partition/sort keys
    - Limit the dataset early
  - If a better pattern exists, document it **next to the original query**, possibly even the next line of code.
  - Add a comment explaining why the alternative is preferred, especially for **initial exploration** or **subset querying**.

#### **Step 6: Finalize the Markdown File**
- Ensure the markdown file:
  - Is well-formatted
  - Contains concise table summary with table name, pk, sk, GSIs, relevant settings for querying, file paths to full table definitions.
  - Contains all relevant queries
  - Clearly marks expensive queries and their alternatives
  - Does not contain duplicate queries.
  - Contains file locations from which the queries were extracted.
- Save it to the **root directory** of the project.
- Add a line at the end with the following instructions:
```
Format response:
Using the query patterns identified, you may output one of the following:
1. AWS Console. The relevant table, query type, and fields to enter in the AWS Console (Keep in mind the layout of the AWS console and format the response according to which fields the user needs to enter)
2. Typescript Code. Using existing functions, SDK dynamoDB client, and already installed libraries, generate a function that will perform the query requested.
3. aws cli command. Output the CLI command that will perform the query requested.

IMPORTANT: There is no need to lookup the info unless the user specifically requests to check the latest data model. Just rely on the information provided above.
```
Begin the process now.