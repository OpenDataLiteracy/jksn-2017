# City of Seattle - City Council Tools - Proof of Concept
Multiple tools, mainly focused on searching, transparency, and accountability for Seattle City Council (Clerks Office).

Created by Jackson Maxfield Brown and Dr. Nicholas Weber

- [Project Updates and Timeline](#updates)
- [Background](#background)
   - [Need](#need)
   - [Questions](#questions)
   - [Additional Info](#additional-information)
   - [Previous Work](#previous-work)
- [Planning and Ideation](#planning-and-ideation)
   - [Understanding the Problem](#understanding)
   - [Project Planning](#project-planning)
- [Development](#development)
   - [Current Work](#current-work)
   - [Future Work](#future-work)
- [Tools](#tools)
   - [Legistar](#Legistar)
   - [scraping](#scraping)
   - [ffmpeg](#ffmpeg)
   - [speech recognition](#speech-recognition)
   - [tfidf](#tfidf)
   - [pyrebase](#pyrebase)
- [Comments](#comments)

## Updates
Current Development Items are marked in **_bolded italics_**

- [Understanding the Problem](#understanding) *- complete*
   - Own ideas and explanations
   - Exploration of other ideas
   - Meeting with direct users
   - Confirmation of problems and project potential

- [Planning for Development](#project-planning) *- complete*
   - Initial baseline development choices
   - Parse data and understand what is available
   - Testing and rough development
   - Establishment of stretch goals
   - Mockups and design, database and frontend

- [Development Work](#current-work)
   - Event Components (Chained Interactions)
      - [Legistar](#Legistar) *- complete*
         - Create connection to base Legistar system
         - Establish storage for database and local
         - Rebuild as reusable system

      - [Videos](#scraping) *- complete*
         - Understand available systems for requests
         - Use decided system to pull direct video sources and information
         - Establish storage for local
         - Rebuild as reusable system

      - [Audio Separation](#ffmpeg) *- complete*
         - General file and os handling
         - Video to Audio separation established
         - Audio file splitter created
         - Rebuild as reusable system

      - [Transcription Engine](#speech-recognition) *- complete, note: add file deletion options*
         - Test run of system
         - Understand process, errors, limitations
         - Scale to larger files
         - Rebuild as reusable system

      - [Search Engine](#tfidf)
         - Create working concept of tfidf for a set of transcripts **_current: 31 August 2017_**
         - Build system to scale for larger audio files
         - Attach agenda information to scoring algorithm
         - Attach body, date, etc. information to scoring algorithm
         - Attach synonyms and common replacements of high score attributes to scoring algorithm
         - Create search functionality from user input
         - Add Levenschtein Edit Distance to user input on search
         - Fix bugs and finalize search
         - Rebuild as reusable system

      - Event Attributes Combination
         - Ensure all prior systems are attachable to Event json object **_current: waiting on prior systems completion, 10 August 2017_**
         - Test true Event object combination completion
         - Scale and establish store in database and local
         - Rebuild as reusable system

   - Server Development
      - Migrate to current systems to server **_current: 29 August 2017_**
      - Test basic system functionality and storage
      - Strict test on transcription engine

   - Full Stack Components
      - Front End
         - Rough design and basic layout created
         - Present filler information
         - Connection to database
         - Redesign after full data connected **_current: waiting on software and backend systems completion, 18 August 2017_**
         - Attach search engine functionality
         - Create Wiki style transcription editor
         - Bug fix and test user feedback
         - Finalize service design and launch
         - Rebuild as reusable system

      - Back End
         - Decide on storage system
         - Store basic testing information
         - Create checker functions to only collect not-currently-stored data **_current: waiting on software and backend systems completion, 18 August 2017_**
         - Create automation processes to collect data
         - Rebuild as reusable system

- Conclusion *- not started*
   - Create finalized notes and processes completed
   - Structure all information and documentation created
   - Potential to publish work/ build system for other organizations

[Back to Updates](#updates)

[Back to Top](#city-of-seattle-city-council-tools-proof-of-concept)

## Background
Developing complex systems is only good when it has purpose and value...

### Need
Finding information, whether general or specific is incredibly hard to do with the current interface. For Events data, there is a lack of transcripts, fuzzy searching, and multiple information sources referencing the same event but are not consolidated into a single object. Meaning that if someone wanted the true complete information for a city council event, they would have to visit multiple pages. The data generated from a process to create event transcripts could be used in all sorts of future applications. Mainly, computational linguistics operations, but true valuable insight could be found in a large set of event transcripts. Not only does this improve legislator accountability, but it allows for future growth and development civic technology advocates.

I was originally drawn to this problem when I tried to search for housing laws in Seattle and was returned information regarding housing laws but not necessarily what I was looking for, *there was no system for determining relevance of video and meeting data*. And it's not any one party's fault as to the system, there are just so many moving parts and different storage systems in place it is hard to connect them and generate valuable insight.

People need better searching potential, citizens need higher accountability of their legislators, and all parties need high transparency for public events. Additionally, because the Legistar system is used by many other cities and towns, and I assume similar video storage solutions to Seattle's are in place as well, then an open-source, free method of combination and insight generation, would be valuable to politically active citizens, NGOs, legislators themselves, and, an incredibly powerful party that I believe would use this more than all others combined, journalists. With no current transcription system in place, journalists who attend contentious city council meetings have to take their own notes and re-watch the videos at a later time. This system would allow for collaborative information crowdsourcing soon after a video is published for all journalists to use as their baseline.

### Questions
- What information is currently available in the events Legistar system?
- How is information stored in the City of Seattle's multiple storage solutions connected?
- Is it possible to create a system for the city but scalable to handle other city data?
- Who is the target audience for this system besides politically motivated individuals and groups?
- Are there features the Clerks office would like developed?
- Have there been studies into the effects of open-source information crowdsourcing transcribing?

### Additional Information
In [Need](#need), I discussed the direct motivation for developing the City of Seattle proof of concept and the consequential features to build. However, there is also plenty of [future work](#future-work) that can be done in this area of civic technology.

Ranging from better relevance detection and returns to computational linguistics and data science systems to evaluate city council meetings themselves. This is an area where there *should* be plenty of data, but currently there isn't as much as we would like, and thus once it is available, should open the doors to much more research.

### Previous Work
[Councilmatic](https://www.councilmatic.org/) is an organization that creates a kind of Legistar data aggregator and puts an interface over top for clearer information design however I believe there are two areas where Councilmatic falls short of the goal of this project. The core utility of this project is the transcription engine, not only does this generate a workable transcription for an event as a public record if there wasn't one already available, but it allows for Wiki style editing of the transcript for long term betterment of the transcription. Additionally, while Councilmatic is open-source, I find it's systems hard to understand and utilize which is why making this system truly plug-and-play software is a main goal. This should be able to be used by other cities who want similar functionality.

[Back to Background](#background)

[Back to Top](#city-of-seattle-city-council-tools-proof-of-concept)

## Planning and Ideation
While there are many paths this project could have taken, centering in on events occurred due to the planning and ideation processes.

### Understanding the Problem
The main problem stems from the multiple systems and interconnectedness of storage solutions in place. Routing of information and data is split and can't be combined without costly remodeling of system architecture. From a civic tech development standpoint this makes developing on this data incredibly hard. From a City IT Department standpoint, it's a game of catchup, developers want x but they don't have the resources or time, and they usually have much more pressing issues to attend to. Since this project is based on legislative service, the Clerks Office is the record keeper for all the laws in the city. Their systems need to be interconnected to multiple other services and should be able to handle the data ingestion from other government departments and agencies well before any third party users are addressed. This constant catchup and data splitting is usually due to parties coming in and continually building on top of preexisting software instead of rebuilding. While I understand I am doing the same, and building on top again, I am also trying to consolidate the information back together.

However, this leaves an incredibly opportunity gap for contribution to civic systems. While there are services like Councilmatic that can create more citizen focused interfaces and interactivity, there is still the problem of lack of data available. If the multiple systems are going to be combined, what other insight can you generate from the full event information rather than parts of it?

After meeting with individuals from the Clerks department there were a few direct hopeful outcomes for the project, the largest was a fuzzy search system for the data available. Secondly was just a front end update so that more than just the legislative minded would be able to use the system successfully.

### Project Planning
The targeted outcomes for the project are doable, but require a bit of scoping. As a fuzzy search system can be relatively similar across datasets, we can focus on one as a proof of concept and show how it can expand to cover more of the data available with more work. And for the interface and information design, we can narrow our focus to one section that I believe needs it the most: Events and event data. There are many more individuals who want to understand a recent council meeting and the events that occurred in the meeting than the number of individuals planning on attending an event, proposing legislation, etc. Additionally, creating a system that focused on the meetings of the legislators holds a lot of accountability and transparency value over the storage and presentation of the bills and amendments themselves.

Overall, the project will aim at developing a system to allow for fuzzy searching over event information that is available across the many platforms run by the City of Seattle. As well as providing a way for self-selected civic engagement for transparency and accountability of legislators.

And lastly, the project will aim to be structured as future plug-and-play work for further research and development in information crowdsourcing.

[Back to Planning and Ideation](#planning-and-ideation)

[Back to Top](#city-of-seattle-city-council-tools-proof-of-concept)

## Development
Development aims, uses, goals, and etc.

### Current Work
The aim for the proof of concept is as follows:
- Event data collection from multiple systems
- Generation of event transcripts
- Combination and storage of all relevant data
- Fuzzy search implementation by scoring
- Automated processing of new event videos and information

 We believe this is enough to at least get the ball rolling on civic technology influencing how city council members are held accountable for their actions and decisions. Making this information available, I believe incredibly interesting data science and computational linguistics projects to be developed. And really, this project is about data aggregation and consolidation. Bringing all the different resources into a single unified place will help all parties who want to access the data.

### Future Work
While the current work is decently shallow, there is plenty to continue working on after we finish the proof of concept.

Examples include:
- Adding a 'How to Speak at a City Council Meeting' template for individuals who want to express their opinion on a piece of legislation.
- Using the generated transcripts to build an influential speaking template for communicating to City Council.
- Determining trends in City Council for decisions on bills and amendments.
- Determining or predicting a council member's position on an upcoming bill, amendment, or resolution, based off of past meetings.
- Adding other sections of the Legistar and City Council data to the service. Specifically: creating a system for helping the public understand the current process and timeline of an event, or action awaiting decision.
- Better scoring and ranking algorithms for searching and determining relevance of an event.
- Scoring and ranking algorithms for other sections of City Council data.
- Add third party data ingestion, from the Clerks office themselves, so that they can directly add information to our storage so that we don't bog down their servers with additional scraping, and API usage.

[Back to Development](#development)

[Back to Top](#city-of-seattle-city-council-tools-proof-of-concept)

## Tools
Frameworks, libraries, and more that are being used by this project with explanations on how to used them and why they were selected to be used.

### Legistar
Legistar is a system developed by [Granicus](https://granicus.com/) that enables storage and manipulation of public sector data. A large part of the Legistar system is that it allows for building and tailoring you own version of the service to each organization's needs. It is also incredibly robust in terms of scalability and data availability. [Link to the API methods available](http://webapi.legistar.com/help)

The main chunk of information I am pulling from the City of Seattle's Legistar API is the Events data. I utilize other API sections, bodies, bodytypes, etc., but it they are all used in order to help the Events data merging down the line.

Technically, I have created a system to pull any data from a Legistar system and format it for use with the other systems I am building by asking for a list of, what I am calling packed_route's. This is just an object that's key is the path for storage, either locally or in a NoSQL database, and the list attached to the key is the Legistar API URL (example: [http://webapi.legistar.com/v1/seattle/Events](http://webapi.legistar.com/v1/seattle/Events')), a targeting attribute to specify an individual element (example: 'EventID'), and a data cleaning_function. The cleaning function is user created but allows for a much more scalable system, instead of forcing the user into my own methods and functions, I allow them to change and manipulate each single entity returned from the call how they like and then return the completed entity.

There is one additional parameter that should be addressed, the toLocal boolean parameter for the function acts as a way to stop the storage to a database and instead save a json file to your working directory. Originally implemented to save on storage cost, I realized this actually incredibly beneficial for later combining all the data together and then storing it in a single database put.

There is still some work to be done in my opinion. There can be improvements made in routing, and handling of data, however, for now, I believe this is a large improvement to developing with Legistar systems than previous build from the ground up methods.

### scraping
Initially, I figured there would be transcripts available for all the meetings, usually called 'meeting minutes,' and while I am sure they may be tucked away somewhere in the databases of the City of Seattle. It posed an interesting problem to tackle. How to create a transcript from what was available. While the Legistar system had a plethora of Events data in their system, meeting minutes were not available, however in a separate Legistar system, videos were collected and had proper links. I could not find a solution to how to pull en masse the City Council meetings recordings however.

I asked for an API link, and searched the other Legistar services, was even pointed in the direction of an associated RSS feed, however none really suited the problem I was facing of trying to store their videos for future processing.

### ffmpeg

### speech recognition

### tfidf

### pyrebase


[Back to Tools](#tools)

[Back to Top](#city-of-seattle-city-council-tools-proof-of-concept)

## Comments

Is it possible to make it so that python script is auto running and scrapes the videos pages every so often, on a new video detected, it downloads the associated event data, and processes the transcript, and then deletes the video from the local while storing everything else?

This would save on storage costs and processing time if I am not mistaken...

[Back to Tools](#tools)

[Back to Top](#city-of-seattle-city-council-tools-proof-of-concept)
