

Content Composer is a new project that I am creating to be an open source package. 
It's goal is to help users build artifacts, like articles, books, stories, podcasts, etc. with the help of AI.

# Recipes

To accomplish that, the user can edit different recipes, that will generate the desired artifact.
These recipes can be: 

## one-shot (i.e. an article)

In this case, there will be only one round-trip between the user and the AI.

## multi-shot (i.e. a book)

In this case, there will be multiple round-trips between the user and the AI.
This can be accomplished in several ways, such as:

- a langgraph workflow
- the use of the supervisor package

### example - book

- Write a one-page briefing about the topic of the book and main characters.
- Write a plan for the chapters of the book with their titles and brief description of the plot.
- Write each of the chapters of the book
- Review the book and make sure it is consistent and well written.

### example - podcast episode

- Write a one-page briefing about the topic of the podcast and main characters.
- Write a brief on what needs to be covered in the podcast episode (sections).
- Write a transcript for each section.
- Review the podcast and make sure it is consistent and well written.
- Get the voices for each section using text to speech
- Export the podcast

# Context

The user might want to provide context to the AI for executing the request, in the form of files, links and / or text. 
This project will use content-core to extract the content from the files and links provided by the user.

# Feedback during the process

The creation process can be done 100% automatically or it can ask the user to approve after each step.
If it's configured to ask for approval, the user will be able to approve or reject each step using Langgraph's Human In the Loop strategy

# UI

We will also need a UI (based on Streamlit) to enable users to define their recipes (they are yaml files that can be downloaded from the repository or created manually)
This file designs each of the steps as in the examples above and points to the prompts for each step.





