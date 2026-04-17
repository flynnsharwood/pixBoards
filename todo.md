
to do

modularise the program
fix images not showing
ability to save boards information to disk. this might turn out to be unnecessary if this doesn't take as much time. 
fix the pagination isssues
    get the pagination html part, the number of pages from the board instance.
    index links do not link to 1st pages 
    index links also do not work as links. they need to be right clicked, and can't be clicked and reached.
    the problem is in master index and index files for normal case, it is a problem for just the index in imgList case
    all boards have 42 pages, despite not having the links or the html files for them. 
    problem is with the pagination html, not the actual pagination.
add the older utilities back
    upload functions
    psycopg2 integration
    random utilities
hashmapping setup