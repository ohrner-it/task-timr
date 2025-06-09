# timr API

timr API for time tracking

# Base URL


| URL | Description |
|-----|-------------|
| https://api.timr.com/v0.2/ |  |


# Authentication



## Security Schemes

| Name              | Type              | Description              | Scheme              | Bearer Format             |
|-------------------|-------------------|--------------------------|---------------------|---------------------------|
| BearerAuthentication | http |  | bearer | uuid |

# APIs

## GET /users

fetches Users

List all Users the authenticated user/authtoken has access to. The entries can be filtered by the provided query parameters, all of which are optional. The number of entries returned is capped by the page size limit. This end point uses cursor pagination. If more entries would be found for a given query, the result envelope contains a 'next_page_token' field with a token that can be used to fetch the next page.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | False | pass a user name to filter entries by the user name |
| entry_date_from | string | False | pass entry_date_from to show all users entered on or after defined day |
| entry_date_to | string | False | pass entry_date_from to show all users entered on or before defined day |
| resign_date_from | string | False | pass resign_date_from to show all users resigned on or after defined day |
| resign_date_to | string | False | pass resign_date_to to show all users resigned on or before defined day |
| resigned | boolean | False | pass parameter resigned true/false to show all users who are resigned/not resigned |
| employee_number | string | False | pass an employee_number to show users with the corresponding employee number |
| page_token | string | False | Token for retrieving the next page. This token is provided in the response of the previous page as next_page_token |
| limit | integer | False | pass a value to change the maximum number of entries returned in a single page (at max 500). |
| sort_direction |  | False | pass a direction in which the entries returned will be sorted in |
| sort_by | string | False | By default sorted by:
 * Lastname
 * Firstname 
 * Id

pass a property by which the returned entries will be sorted if you want a different order
 |


### Responses

#### 200


search results matching criteria


[UsersPage](#userspage)







#### 400


bad input parameter


[Error](#error)







## POST /users

create an User

Creates a new User based on the data provided in the request body.




### Request Body

[UserCreate](#usercreate)







### Responses

#### 201


created User entity


[User](#user)







#### 400


bad input parameter


[Error](#error)







## GET /users/{id}

get a single user

Retrieves a single User based on its User ID.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True |  |


### Responses

#### 200


search results matching criteria


[User](#user)







#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## PATCH /users/{id}

updates a single User

Updates the User specified by the id with the fields provided in the request body.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True |  |


### Request Body

[UserUpdate](#userupdate)







### Responses

#### 200


user successfully updated


[User](#user)







#### 400


bad request


[Error](#error)







#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## GET /users/{id}/working-time-accounts/{date}

get a user's working time accounts

Retrieves a User's working time accounts balance to a given day.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True |  |
| date | string | True |  |


### Responses

#### 200


search results matching criteria


[WorkingTimeAccounts](#workingtimeaccounts)







#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## GET /users/{id}/work-schedule-model

get a User's Work-Schedule-Model

Retrieves the corresponding Work-Schedule-Model with durations in minutes based on a User's ID


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True |  |


### Responses

#### 200


search results matching criteria


[WorkScheduleModel](#workschedulemodel)







#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## GET /work-schedule-models

fetches Work Schedule Models

List all Work Schedule Models the authenticated user/authtoken has access to. The entries can be filtered by the provided query parameters, all of which are optional. The number of entries returned is capped by the page size limit. This end point uses cursor pagination. If more entries would be found for a given query, the result envelope contains a 'next_page_token' field with a token that can be used to fetch the next page.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| page_token | string | False | Token for retrieving the next page. This token is provided in the response of the previous page as next_page_token |
| limit | integer | False | optionally, pass a value to change the maximum number of entries returned in a single page (at max 500). |
| sort_direction |  | False | optionally, pass a direction in which the entries returned will be sorted in (based on the WorkScheduleModel's name) |
| sort_by | string | False |  |


### Responses

#### 200


search results matching criteria


[WorkScheduleModelsPage](#workschedulemodelspage)







#### 400


bad input parameter


[Error](#error)







## GET /work-schedule-models/{id}

gets a single Work Schedule Model

Retrieves a single Working Schedule Model based on its id.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True |  |


### Responses

#### 200


search results matching criteria


[WorkScheduleModel](#workschedulemodel)







#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## DELETE /work-schedule-models/{id}

deletes a single Work Schedule Model

Deletes a single Work Schedule Model based on its id.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True |  |


### Responses

#### 204


Empty response indicating that delete was successful




#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## GET /working-times

fetches Working Times

List all Working Times the authenticated user/authtoken has access to. The entries can be filtered by the provided query parameters, all of which are optional. The number of entries returned is capped by the page size limit. This end point uses cursor pagination. If more entries would be found for a given query, the result envelope contains a 'next_page_token' field with a token that can be used to fetch the next page.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| notes | string | False | pass a search string to filter entries containing this string in their notes |
| start_from | string | False | pass a date to filter entries started from this day on |
| start_to | string | False | pass a date to filter entries started up to (including) this day |
| last_modified_after | string | False | pass a datetime to filter entries modified after this instant |
| working_time_types | array | False | pass one or more ids of WorkingTimeTypes to restrict entries based on these types |
| working_time_type_categories | array | False | optionally, pass one or more WorkingTimeTypeCategories to restrict entries based on these categories |
| statuses | array | False | pass one or more statuses to filter entries based on their status |
| users | array | False | pass one or more user ids to restrict entries based on the user they are associated to |
| changed | boolean | False | pass a boolean to filter entries based on whether they have been changed by the user or not |
| page_token | string | False | Token for retrieving the next page. This token is provided in the response of the previous page as next_page_token |
| limit | integer | False | pass a value to change the maximum number of entries returned in a single page (at max 500). |
| sort_direction |  | False | pass a direction in which the entries returned will be sorted in |
| sort_by | string | False | By default sorted by:
 * start
 * Id

pass a property by which the returned entries will be sorted
 |


### Responses

#### 200


search results matching criteria


[WorkingTimesPage](#workingtimespage)







#### 400


bad input parameter


[Error](#error)







## POST /working-times

create a Working Time

Creates a new Working Time based on the data provided in the request body.




### Request Body

[WorkingTimeCreate](#workingtimecreate)







### Responses

#### 201


created Working Time entity


[WorkingTime](#workingtime)







#### 400


bad input parameter


[Error](#error)







## GET /working-times/{id}

gets a single Working Time

Retrieves a single Working Time based on its id.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True |  |


### Responses

#### 200


search results matching criteria


[WorkingTime](#workingtime)







#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## PATCH /working-times/{id}

updates a single Working Time

Updates the Working Time specified by the id with the fields provided in the request body.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True |  |


### Request Body

[WorkingTimeUpdate](#workingtimeupdate)







### Responses

#### 200


search results matching criteria


[WorkingTime](#workingtime)







#### 400


bad request


[Error](#error)







#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## DELETE /working-times/{id}

deletes a single Working Time

Deletes a single Working Time based on its id.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True |  |


### Responses

#### 204


Empty response indicating that delete was successful




#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## GET /working-times:deleted

Get deleted working times

List all deleted Working Times the authenticated user/authtoken has access to, optionally filtered by last_modified. The number of entries returned is capped by the page size limit. This end point uses cursor pagination. If more entries would be found for a given query, the result envelope contains a 'next_page_token' field with a token that can be used to fetch the next page.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| last_modified | string | False | optionally, pass a datetime to filter entries modified after this instant |
| page_token | string | False | Token for retrieving the next page. This token is provided in the response of the previous page as next_page_token |
| limit | integer | False | optionally, pass a value to change the maximum number of entries returned in a single page (at max 500). |
| sort_direction |  | False | optionally, pass a direction in which the entries returned will be sorted in |
| sort_by | string | False | By default sorted by:
 * last_modified
 * Id
optionally, pass a property by which the returned entries will be sorted if you want a different order
 |


### Responses

#### 200


Successful response


[DeletedEntryWithMetadataPage](#deletedentrywithmetadatapage)







#### 400


bad input parameter


[Error](#error)







## GET /project-times

fetches Project Times

List all Project Times the authenticated user/authtoken has access to. The entries can be filtered by the provided query parameters, all of which are optional. The number of entries returned is capped by the page size limit. This end point uses cursor pagination. If more entries would be found for a given query, the result envelope contains a 'next_page_token' field with a token that can be used to fetch the next page.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| notes | string | False | pass a search string to filter entries containing this string in their notes |
| start_from | string | False | pass a date to filter entries started from this day on |
| start_to | string | False | pass a date to filter entries started up to (including) this day |
| last_modified_after | string | False | pass a datetime to filter entries modified after this instant |
| task | string | False | pass a tasks id to restrict entries based on its value |
| traverse_task_tree | boolean | False | pass this parameter with value true/false to filter just by task specified or also traverse its task tree |
| billable | boolean | False | pass this parameter with value true/false to show just entries/no entries which are billable |
| statuses | array | False | pass one or more statuses to filter entries based on their status |
| users | array | False | pass one or more user ids to restrict entries based on the user they are associated to |
| changed | boolean | False | pass a boolean to filter entries based on whether they have been changed by the user or not |
| page_token | string | False | Token for retrieving the next page. This token is provided in the response of the previous page as next_page_token |
| limit | integer | False | pass a value to change the maximum number of entries returned in a single page (at max 500). |
| sort_direction |  | False | pass a direction in which the entries returned will be sorted in |
| sort_by | string | False | By default sorted by:
 * start
 * Id
 |


### Responses

#### 200


search results matching criteria


[ProjectTimesPage](#projecttimespage)







#### 400


bad input parameter


[Error](#error)







## POST /project-times

create a Project Time

Creates a new Project Time based on the data provided in the request body.




### Request Body

[ProjectTimeCreate](#projecttimecreate)







### Responses

#### 201


created Project Time entity


[ProjectTime](#projecttime)







#### 400


bad input parameter


[Error](#error)







## GET /project-times/{id}

gets a single Project Time

Retrieves a single Project Time based on its id.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True |  |


### Responses

#### 200


search results matching criteria


[ProjectTime](#projecttime)







#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## PATCH /project-times/{id}

updates a single Project Time

Updates the Project Time specified by the id with the fields provided in the request body.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True |  |


### Request Body

[ProjectTimeUpdate](#projecttimeupdate)







### Responses

#### 200


search results matching criteria


[ProjectTime](#projecttime)







#### 400


bad request


[Error](#error)







#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## DELETE /project-times/{id}

deletes a single Project Time

Deletes a single Project Time based on its id.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True |  |


### Responses

#### 204


Empty response indicating that delete was successful




#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## GET /project-times:deleted

Get deleted project times

List all deleted Project Times the authenticated user/authtoken has access to, optionally filtered by last_modified. The number of entries returned is capped by the page size limit. This end point uses cursor pagination. If more entries would be found for a given query, the result envelope contains a 'next_page_token' field with a token that can be used to fetch the next page.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| last_modified | string | False | optionally, pass a datetime to filter entries modified after this instant |
| page_token | string | False | Token for retrieving the next page. This token is provided in the response of the previous page as next_page_token |
| limit | integer | False | optionally, pass a value to change the maximum number of entries returned in a single page (at max 500). |
| sort_direction |  | False | optionally, pass a direction in which the entries returned will be sorted in |
| sort_by | string | False | By default sorted by:
 * last_modified
 * Id
optionally, pass a property by which the returned entries will be sorted if you want a different order
 |


### Responses

#### 200


Successful response


[DeletedEntryPage](#deletedentrypage)







#### 400


bad input parameter


[Error](#error)







## GET /tasks

fetches Tasks

List all Tasks the authenticated user/authtoken has access to. The entries can be filtered by the provided query parameters, all of which are optional. The number of entries returned is capped by the page size limit. This end point uses cursor pagination. If more entries would be found for a given query, the result envelope contains a 'next_page_token' field with a token that can be used to fetch the next page.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| parent_task_id | string | False | pass task's id to restrict entries having this task as a parent task |
| traverse_task_tree | boolean | False | pass this parameter with value true/false to traverse the whole task tree |
| name | string | False | pass a user name to filter entries by the user name |
| bookable | boolean | False | pass this parameter with value true/false to show just entries/no entries which are billable |
| billable | boolean | False | pass this parameter with value true/false to show just entries/no entries which are billable |
| page_token | string | False | Token for retrieving the next page. This token is provided in the response of the previous page as next_page_token |
| limit | integer | False | pass a value to change the maximum number of entries returned in a single page (at max 500). |
| sort_direction |  | False | pass a direction in which the entries returned will be sorted in |
| sort_by | string | False | By default sorted by:
 * breadcrumbs
 * id

pass a property by which the returned entries will be sorted if you want a different order
 |


### Responses

#### 200


search results matching criteria


[TasksPage](#taskspage)







#### 400


bad input parameter


[Error](#error)







## POST /tasks

create a Task

Creates a new Task based on the data provided in the request body.




### Request Body

[TaskCreate](#taskcreate)







### Responses

#### 201


created Task entity


[Task](#task)







#### 400


bad input parameter


[Error](#error)







## GET /tasks/{id}

get a single task

Retrieves a single Task based on its Task ID.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True |  |


### Responses

#### 200


search results matching criteria


[Task](#task)







#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## PATCH /tasks/{id}

updates a single Task

Updates the Task specified by the id with the fields provided in the request body.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True |  |


### Request Body

[TaskUpdate](#taskupdate)







### Responses

#### 200


task successfully updated


[Task](#task)







#### 400


bad request


[Error](#error)







#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## GET /tasks/{task_id}/users

fetches Task to User Assignments

List all task to user assignments the authenticated user/authtoken has access to.The number of entries returned is capped by the page size limit. This end point uses cursor pagination. If more entries would be found for a given query, the result envelope contains a 'next_page_token' field with a token that can be used to fetch the next page.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| task_id | string | True |  |
| page_token | string | False | Token for retrieving the next page. This token is provided in the response of the previous page as next_page_token |
| limit | integer | False | pass a value to change the maximum number of entries returned in a single page (at max 500). |
| sort_direction |  | False | pass a direction in which the entries returned will be sorted in |
| sort_by | string | False | By default sorted by:
   * Lastname
   * Firstname 
   * Id
of the assigned user
 |


### Responses

#### 200


search results matching criteria


[TaskToUserAssignmentsPage](#tasktouserassignmentspage)







#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## GET /tasks/{task_id}/users/{user_id}

get a single task to user assignment

Retrieves a single Task based on its Task ID.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| task_id | string | True |  |
| user_id | string | True |  |


### Responses

#### 200


search results matching criteria


[TaskToUserAssignment](#tasktouserassignment)







#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## PUT /tasks/{task_id}/users/{user_id}

create a Task to User Assignment

Creates a new Task to User Assignment for the given user_id based on the data provided in the request body.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| task_id | string | True |  |
| user_id | string | True |  |


### Request Body

[TaskToUserAssignmentCreateAndUpdate](#tasktouserassignmentcreateandupdate)







### Responses

#### 201


created Task to User Assignment


[TaskToUserAssignment](#tasktouserassignment)







#### 400


bad input parameter


[Error](#error)







## PATCH /tasks/{task_id}/users/{user_id}

update a Task to User Assignment

Updates the Task to User Assignment specified by the id with the fields provided in the request body.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| task_id | string | True |  |
| user_id | string | True |  |


### Request Body

[TaskToUserAssignmentCreateAndUpdate](#tasktouserassignmentcreateandupdate)







### Responses

#### 201


updated Task to User Assignment


[TaskToUserAssignment](#tasktouserassignment)







#### 400


bad input parameter


[Error](#error)







## DELETE /tasks/{task_id}/users/{user_id}

deletes a Task to User Assignment

Deletes a Task to User Assignment based on its task_id and user_id.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| task_id | string | True |  |
| user_id | string | True |  |


### Responses

#### 204


Empty response indicating that delete was successful




#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## GET /tasks/{task_id}/leaders

fetches Task to Leader Assignments

List all task to leader assignments the authenticated user/authtoken has access to.The number of entries returned is capped by the page size limit. This end point uses cursor pagination. If more entries would be found for a given query, the result envelope contains a 'next_page_token' field with a token that can be used to fetch the next page.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| task_id | string | True |  |
| page_token | string | False | Token for retrieving the next page. This token is provided in the response of the previous page as next_page_token |
| limit | integer | False | pass a value to change the maximum number of entries returned in a single page (at max 500). |
| sort_direction |  | False | pass a direction in which the entries returned will be sorted in |
| sort_by | string | False | By default sorted by:
   * Lastname
   * Firstname 
   * Id
of the assigned leader
 |


### Responses

#### 200


search results matching criteria


[TaskToLeaderAssignmentsPage](#tasktoleaderassignmentspage)







#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## GET /tasks/{task_id}/leaders/{user_id}

get a single task to leader assignment

Retrieves a single Task based on its Task ID and User ID.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| task_id | string | True |  |
| user_id | string | True |  |


### Responses

#### 200


search results matching criteria


[TaskToLeaderAssignment](#tasktoleaderassignment)







#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## PUT /tasks/{task_id}/leaders/{user_id}

create a Task to Leader Assignment

Creates a new Task to Leader Assignment for the given user_id based on the data provided in the request body.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| task_id | string | True |  |
| user_id | string | True |  |


### Responses

#### 201


created Task to User Assignment


[TaskToLeaderAssignment](#tasktoleaderassignment)







#### 400


bad input parameter


[Error](#error)







## DELETE /tasks/{task_id}/leaders/{user_id}

deletes a Task to Leader Assignment

Deletes a Task to Leader Assignment based on its task_id and user_id.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| task_id | string | True |  |
| user_id | string | True |  |


### Responses

#### 204


Empty response indicating that delete was successful




#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## GET /drive-logs

fetches Drive Logs

List all Drive Logs the authenticated user/authtoken has access to. The entries can be filtered by the provided query parameters, all of which are optional. The number of entries returned is capped by the page size limit. This end point uses cursor pagination. If more entries would be found for a given query, the result envelope contains a 'next_page_token' field with a token that can be used to fetch the next page.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| start_from | string | False | pass a date to filter entries started from this day on |
| start_to | string | False | pass a date to filter entries started up to (including) this day |
| last_modified_after | string | False | pass a datetime to filter entries modified after this instant |
| cars | array | False | pass one or more ids of cars to restrict entries based on these cars |
| drive_log_categories | array | False | pass one or more ids of drive log categories to restrict entries based on these categories |
| statuses | array | False | pass one or more statuses to filter entries based on their status |
| users | array | False | pass one or more user ids to restrict entries based on the user they are associated to |
| details | string | False | pass a String based on which the entries are filtered if it is contained in the properties route, purpose or visited |
| changed | boolean | False | pass a boolean to filter entries based on whether they have been changed by the user or not |
| has_track | boolean | False | pass a boolean to filter entries based on whether they have a track or not |
| page_token | string | False | Token for retrieving the next page. This token is provided in the response of the previous page as next_page_token |
| limit | integer | False | pass a value to change the maximum number of entries returned in a single page (at max 500). |
| sort_direction |  | False | pass a direction in which the entries returned will be sorted in |
| sort_by | string | False | By default sorted by:
 * start
 * las_modified_after
 * id
 |


### Responses

#### 200


search results matching criteria


[DriveLogsPage](#drivelogspage)







#### 400


bad input parameter


[Error](#error)







## POST /drive-logs

create a Drive Log

Creates a new Drive Log based on the data provided in the request body.




### Request Body

[DriveLogCreate](#drivelogcreate)







### Responses

#### 201


created Drive Log entity


[DriveLog](#drivelog)







#### 400


bad input parameter


[Error](#error)







## GET /drive-logs/{id}

gets a single Drive Log

Retrieves a single Drive Log based on its id.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True |  |


### Responses

#### 200


search results matching criteria


[DriveLog](#drivelog)







#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## PATCH /drive-logs/{id}

updates a single Drive Log

Updates the Drive Log specified by the id with the fields provided in the request body.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True |  |


### Request Body

[DriveLogUpdate](#drivelogupdate)







### Responses

#### 200


search results matching criteria


[DriveLog](#drivelog)







#### 400


bad request


[Error](#error)







#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## GET /drive-logs:deleted

Get deleted drive logs

List all deleted Working Time Requests the authenticated user/authtoken has access to, optionally filtered by last_modified. The number of entries returned is capped by the page size limit. This end point uses cursor pagination. If more entries would be found for a given query, the result envelope contains a 'next_page_token' field with a token that can be used to fetch the next page.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| last_modified | string | False | optionally, pass a datetime to filter entries modified after this instant |
| page_token | string | False | Token for retrieving the next page. This token is provided in the response of the previous page as next_page_token |
| limit | integer | False | optionally, pass a value to change the maximum number of entries returned in a single page (at max 500). |
| sort_direction |  | False | optionally, pass a direction in which the entries returned will be sorted in |
| sort_by | string | False | By default sorted by:
 * last_modified
 * Id
optionally, pass a property by which the returned entries will be sorted if you want a different order
 |


### Responses

#### 200


Successful response


[DeletedEntryPage](#deletedentrypage)







#### 400


bad input parameter


[Error](#error)







## GET /cars

fetches Cars

List all Cars the authenticated user/authtoken has access to. The entries can be filtered by the provided query parameters, all of which are optional. The number of entries returned is capped by the page size limit. This end point uses cursor pagination. If more entries would be found for a given query, the result envelope contains a 'next_page_token' field with a token that can be used to fetch the next page.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| name_or_plate | string | False | pass a String based on which the entries are filtered if it is contained in the properties name or plate |
| usable | boolean | False | pass a boolean to filter entries based on whether the car is usable or not |
| page_token | string | False | Token for retrieving the next page. This token is provided in the response of the previous page as next_page_token |
| limit | integer | False | pass a value to change the maximum number of entries returned in a single page (at max 500). |
| sort_direction |  | False | pass a direction in which the entries returned will be sorted in |
| sort_by | string | False | By default sorted by:
 * name
 * id
 |


### Responses

#### 200


search results matching criteria


[CarsPage](#carspage)







#### 400


bad input parameter


[Error](#error)







## GET /cars/{id}

gets a single Car

Retrieves a single Car based on its id.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True |  |


### Responses

#### 200


search results matching criteria


[Car](#car)







#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## GET /drive-log-categories

fetches Drive Log Categories

List all Drive Log Categories the authenticated user/authtoken has access to. The entries can be filtered by the provided query parameters, all of which are optional. The number of entries returned is capped by the page size limit. This end point uses cursor pagination. If more entries would be found for a given query, the result envelope contains a 'next_page_token' field with a token that can be used to fetch the next page.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| page_token | string | False | Token for retrieving the next page. This token is provided in the response of the previous page as next_page_token |
| limit | integer | False | pass a value to change the maximum number of entries returned in a single page (at max 500). |
| sort_direction |  | False | pass a direction in which the entries returned will be sorted in |
| sort_by | string | False | By default sorted by:
 * name
 * id
 |


### Responses

#### 200


search results matching criteria


[DriveLogCategoriesPage](#drivelogcategoriespage)







#### 400


bad input parameter


[Error](#error)







## GET /drive-log-categories/{id}

gets a single Drive Log Category

Retrieves a single Drive Log Category based on its id.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True |  |


### Responses

#### 200


search results matching criteria


[DriveLogCategory](#drivelogcategory)







#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## GET /drive-logs/{id}/track

gets the Track of a Drive Log if present

Retrieves Drive Log's Track based on its id.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True | drive log id |


### Responses

#### 200


search results matching criteria


[Track](#track)







#### 400


bad request


[Error](#error)







#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## POST /drive-logs/{id}/track

create a Track for a Drive Log

Creates a new Track for a Drive Log based on the waypoints provided in the request body.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True | drive log id |


### Request Body

[Track](#track)







### Responses

#### 201


created Working Time entity


[Track](#track)







#### 400


bad input parameter


[Error](#error)







## PUT /drive-logs/{id}/track

updates a Drive Log's Track

Updates the Track specified by the id of a Drive Log with the waypoints provided in the request body.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True | drive log id |


### Request Body

[Track](#track)







### Responses

#### 200


working time date span successfully updated


[Track](#track)







#### 400


bad request


[Error](#error)







#### 403


not allowed


[Error](#error)







## DELETE /drive-logs/{id}/track

deletes a Drive Log's Track

Deletes a single Track based on a Drive Log's id.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True | drive log id |


### Responses

#### 204


Empty response indicating that delete was successful




#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## GET /working-time-requests

fetches Working Time Requests

List all Working Times Requests the authenticated user/authtoken has access to. The entries can be filtered by the provided query parameters, all of which are optional. The number of entries returned is capped by the page size limit. This end point uses cursor pagination. If more entries would be found for a given query, the result envelope contains a 'next_page_token' field with a token that can be used to fetch the next page.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| from | string | False | pass a date to filter entries started from this day on |
| to | string | False | pass a date to filter entries started up to (including) this day |
| last_modified_after | string | False | pass a datetime to filter entries modified after this instant |
| working_time_types | array | False | pass one or more ids of Working Time Types to restrict entries based on these types |
| statuses | array | False | pass one or more statuses to filter entries based on their status |
| users | array | False | pass one or more user ids to restrict entries based on the user they are associated to |
| page_token | string | False | Token for retrieving the next page. This token is provided in the response of the previous page as next_page_token |
| limit | integer | False | pass a value to change the maximum number of entries returned in a single page (at max 500). |
| sort_direction |  | False | pass a direction in which the entries returned will be sorted in |
| sort_by | string | False | By default sorted by:
 * start
 * Id
 |


### Responses

#### 200


search results matching criteria


[WorkingTimeRequestsPage](#workingtimerequestspage)







#### 400


bad input parameter


[Error](#error)







## GET /working-time-requests/{id}

gets a single Working Time Request

Retrieves a single Working Time Request based on its id.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True |  |


### Responses

#### 200


search results matching criteria


[WorkingTimeRequest](#workingtimerequest)







#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## DELETE /working-time-requests/{id}

deletes a single Working Time Request

Deletes a single Working Time based on its id.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True |  |


### Responses

#### 204


Empty response indicating that delete was successful




#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## GET /working-time-requests:deleted

Get deleted working time requests

List all deleted Working Time Requests the authenticated user/authtoken has access to, optionally filtered by last_modified. The number of entries returned is capped by the page size limit. This end point uses cursor pagination. If more entries would be found for a given query, the result envelope contains a 'next_page_token' field with a token that can be used to fetch the next page.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| last_modified | string | False | optionally, pass a datetime to filter entries modified after this instant |
| page_token | string | False | Token for retrieving the next page. This token is provided in the response of the previous page as next_page_token |
| limit | integer | False | optionally, pass a value to change the maximum number of entries returned in a single page (at max 500). |
| sort_direction |  | False | optionally, pass a direction in which the entries returned will be sorted in |
| sort_by | string | False | By default sorted by:
 * last_modified
 * Id
optionally, pass a property by which the returned entries will be sorted if you want a different order
 |


### Responses

#### 200


Successful response


[DeletedEntryPage](#deletedentrypage)







#### 400


bad input parameter


[Error](#error)







## GET /working-time-date-spans

fetches Working Time Date Spans

List all Working Times Date Spans the authenticated user/authtoken has access to. The entries can be filtered by the provided query parameters, all of which are optional. The number of entries returned is capped by the page size limit. This end point uses cursor pagination. If more entries would be found for a given query, the result envelope contains a 'next_page_token' field with a token that can be used to fetch the next page.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| from | string | False | pass a date to filter entries started from this day on |
| to | string | False | pass a date to filter entries started up to (including) this day |
| last_modified_after | string | False | pass a datetime to filter entries modified after this instant |
| working_time_types | array | False | pass one or more ids of Working Time Types to restrict entries based on these types |
| users | array | False | pass one or more user ids to restrict entries based on the user they are associated to |
| page_token | string | False | Token for retrieving the next page. This token is provided in the response of the previous page as next_page_token |
| limit | integer | False | pass a value to change the maximum number of entries returned in a single page (at max 500). |
| sort_direction |  | False | pass a direction in which the entries returned will be sorted in |
| sort_by | string | False | By default sorted by:
 * start
 * Id
 |


### Responses

#### 200


search results matching criteria


[WorkingTimeDateSpanPage](#workingtimedatespanpage)







#### 400


bad input parameter


[Error](#error)







## POST /working-time-date-spans

create a Working Time Date Span

Creates a new Working Time Date Span based on the data provided in the request body.




### Request Body

[WorkingTimeDateSpanCreate](#workingtimedatespancreate)







### Responses

#### 201


created Working Time entity


[WorkingTimeDateSpan](#workingtimedatespan)







#### 400


bad input parameter


[Error](#error)







## GET /working-time-date-spans/{id}

gets a single Working Time Date Span

Retrieves a single Working Time Date Span based on its id.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True |  |


### Responses

#### 200


corresponding working time date span entity for the given id


[WorkingTimeDateSpan](#workingtimedatespan)







#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## PATCH /working-time-date-spans/{id}

updates a single Working Time Date Span

Updates the Working Time Date Span specified by the id with the fields provided in the request body.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True |  |


### Request Body

[WorkingTimeDateSpanUpdate](#workingtimedatespanupdate)







### Responses

#### 200


working time date span successfully updated


[WorkingTimeDateSpan](#workingtimedatespan)







#### 204


Empty response indicating that a date span got deleted. This can happen when it is updated to a day where no working hours can be booked.




#### 400


bad request


[Error](#error)







#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## DELETE /working-time-date-spans/{id}

deletes a single Working Time Date Span

Deletes a single Working Time Date Span based on its id.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True |  |


### Responses

#### 204


Empty response indicating that delete was successful




#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## GET /working-time-date-spans:deleted

Get deleted working time requests

List all deleted Working Time Date Spans the authenticated user/authtoken has access to, optionally filtered by last_modified. The number of entries returned is capped by the page size limit. This end point uses cursor pagination. If more entries would be found for a given query, the result envelope contains a 'next_page_token' field with a token that can be used to fetch the next page.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| last_modified | string | False | optionally, pass a datetime to filter entries modified after this instant |
| page_token | string | False | Token for retrieving the next page. This token is provided in the response of the previous page as next_page_token |
| limit | integer | False | optionally, pass a value to change the maximum number of entries returned in a single page (at max 500). |
| sort_direction |  | False | optionally, pass a direction in which the entries returned will be sorted in |
| sort_by | string | False | By default sorted by:
 * last_modified
 * Id
optionally, pass a property by which the returned entries will be sorted if you want a different order
 |


### Responses

#### 200


Successful response


[DeletedEntryWithMetadataPage](#deletedentrywithmetadatapage)







#### 400


bad input parameter


[Error](#error)







## GET /working-time-types

fetches Working Time Types

List all Working Time Types the authenticated user/authtoken has access to. The entries can be filtered by the provided query parameters, all of which are optional. The number of entries returned is capped by the page size limit. This end point uses cursor pagination. If more entries would be found for a given query, the result envelope contains a 'next_page_token' field with a token that can be used to fetch the next page.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | False | filter by name |
| short_name | string | False | filter by short name |
| description | string | False | filter by description |
| categories | array | False | filter by WorkingTimeTypeCategory |
| sub_categories | array | False | filter by WorkingTimeTypeSubCategory |
| edit_units | array | False | filter by WorkingTimeType's DurationUnit |
| archived | boolean | False | pass a boolean to filter entries based on whether they are archived or not |
| recording_modes | array | False | filter entries bAWS on their RecordingMode |
| page_token | string | False | Token for retrieving the next page. This token is provided in the response of the previous page as next_page_token. |
| limit | integer | False | pass a value to change the maximum number of entries returned in a single page (at max 500). |
| sort_direction |  | False | pass a direction in which the entries returned will be sorted in |
| sort_by | string | False | By default sorted by:
 * name
 * Id
 |


### Responses

#### 200


search results matching criteria


[WorkingTimeTypesPage](#workingtimetypespage)







#### 400


bad input parameter


[Error](#error)







## GET /working-time-types/{id}

gets a single Working Time Type

Retrieves a single Working Time Type based on its id.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True |  |


### Responses

#### 200


search results matching criteria


[WorkingTimeType](#workingtimetype)







#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## DELETE /working-time-types/{id}

deletes a single Working Time Type

Deletes a single Working Time Type based on its id.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True |  |


### Responses

#### 204


Empty response indicating that delete was successful




#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## GET /holiday-calendars

fetches Holiday Calendars

List all Holiday Calendars the authenticated user/authtoken has access to.The number of entries returned is capped by the page size limit. This end point uses cursor pagination. If more entries would be found for a given query, the result envelope contains a 'next_page_token' field with a token that can be used to fetch the next page.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| page_token | string | False | Token for retrieving the next page. This token is provided in the response of the previous page as next_page_token |
| limit | integer | False | pass a value to change the maximum number of entries returned in a single page (at max 500). |
| sort_direction |  | False | pass a direction in which the entries returned will be sorted in |
| sort_by | string | False | By default sorted by:
 * Description
 * Id
 |


### Responses

#### 200


search results matching criteria


[HolidayCalendarsPage](#holidaycalendarspage)







#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## GET /holiday-calendars/{id}

gets a single Holiday Calendar

Retrieves a single Holiday Calendar based on its id.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True |  |


### Responses

#### 200


search results matching criteria


[HolidayCalendarPartial](#holidaycalendarpartial)







#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







## GET /holiday-calendars/{id}/holidays

fetches all Holidays of a specific Holiday Calendar

Retrieves a all Holidays of one Holiday Calendar specified by its id. The number of entries returned is capped by the page size limit. This end point uses cursor pagination. If more entries would be found for a given query, the result envelope contains a 'next_page_token' field with a token that can be used to fetch the next page.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | True |  |
| page_token | string | False | Token for retrieving the next page. This token is provided in the response of the previous page as next_page_token |
| limit | integer | False | pass a value to change the maximum number of entries returned in a single page (at max 500). |
| sort_direction |  | False | pass a direction in which the entries returned will be sorted in |
| sort_by | string | False | By default sorted by:
 * Description
 * Id
 |


### Responses

#### 200


search results matching criteria


[HolidaysPage](#holidayspage)







#### 403


not allowed


[Error](#error)







#### 404


not found


[Error](#error)







# Components



## Error



| Field | Type | Description |
|-------|------|-------------|
| code | number |  |
| message | string |  |


## Duration



| Field | Type | Description |
|-------|------|-------------|
| type |  |  |
| minutes | integer | Net minutes of the recording. In case of type 'half_day' or 'full_day' these get calculated automatically, based on WorkTimeSchedule configured for User
 |
| minutes_rounded | integer | Net minutes rounded to the default setting configured. In case of type 'half_day' or 'full_day' these get calculated automatically, based on WorkTimeSchedule configured for User
 |


## DurationType





## DateTime


RFC 3339 date-time (ISO-8601)




## LocalDate


RFC 3339 date (ISO-8601)




## LocalTime


time of day (ISO-8601)




## BreakTime





## BreakTimeUpdate





## BreakTimeManual



| Field | Type | Description |
|-------|------|-------------|
| type | string |  |
| duration_minutes | integer | Duration of break in minutes. Please make sure it matches the duration between 'start' and 'end' if the properties are also given. |
| start |  | start and end are optional. To avoid discrepancies in the duration given in duration_minutes and the time between start and end the preferable way is to only provide duration_minutes. |
| end |  | start and end are optional. To avoid discrepancies in the duration given in duration_minutes and the time between start and end the preferable way is to only provide duration_minutes. |


## BreakTimeOngoing



| Field | Type | Description |
|-------|------|-------------|
| type | string |  |
| start |  |  |


## BreakTimeAutomatic



| Field | Type | Description |
|-------|------|-------------|
| type | string |  |
| duration_minutes | integer | Duration of break in minutes |
| start |  |  |
| end |  |  |


## BreakTimeType





## UserPartial



| Field | Type | Description |
|-------|------|-------------|
| id | string |  |
| firstname | string |  |
| lastname | string |  |
| fullname | string |  |
| email | string | Email address must be either valid or null. |
| employee_number | string |  |
| external_id | string |  |


## User





## UsersPage





## UsersSortColumn





## UserUpdate



| Field | Type | Description |
|-------|------|-------------|
| login | string |  |
| firstname | string |  |
| lastname | string |  |
| email | string |  |
| entry_date |  |  |
| resign_date |  |  |
| employee_number | string |  |
| external_id | string |  |


## UserCreate





## HolidayCalendarPartial



| Field | Type | Description |
|-------|------|-------------|
| id | string |  |
| description | string |  |


## HolidayCalendarsPage





## HolidayCalendarsSortColumn





## Holiday



| Field | Type | Description |
|-------|------|-------------|
| date |  |  |
| description | string |  |
| half_day | boolean |  |


## HolidaysPage





## HolidaysSortColumn





## WorkingTimeAccounts



| Field | Type | Description |
|-------|------|-------------|
| last_balance_date | string | date of last balance |
| time_account |  |  |
| overtime |  |  |
| allowances |  |  |


## TimeAccount



| Field | Type | Description |
|-------|------|-------------|
| balance_last_period_minutes | integer |  |
| duration_actual_minutes | integer | sum of durations in current period |
| duration_target_minutes | integer | target duration in current period |
| balance_current_period_minutes | integer | difference between target duration and actual duration |
| balance_total_minutes | integer | total duration until balancing date |
| work_from_home_days_full | integer | complete days worked from home in current period |
| work_from_home_days_partial | integer | partial days worked from home in current period |
| flex_time_indicator |  |  |


## Overtime



| Field | Type | Description |
|-------|------|-------------|
| balance_last_period_minutes | integer |  |
| balance_current_period_minutes | integer |  |
| balance_total_minutes | integer |  |


## Allowances



| Field | Type | Description |
|-------|------|-------------|
| balance_last_period_minutes | integer |  |
| balance_current_period_minutes | integer |  |
| balance_total_minutes | integer |  |


## FlexTimeIndicator





## WorkScheduleModelPartial



| Field | Type | Description |
|-------|------|-------------|
| id | string |  |
| name | string |  |


## WorkScheduleModel





## WorkScheduleModelsPage





## WorkScheduleModelSortColumn





## Location



| Field | Type | Description |
|-------|------|-------------|
| lat | number |  |
| lon | number |  |
| timestamp |  |  |
| formatted_address | string |  |


## Platform





## WorkingTimeStatus





## WorkScheduleModelType





## DailyWorkSchedule



| Field | Type | Description |
|-------|------|-------------|
| target_duration_minutes | integer | value in minutes |
| normal_working_times | array | this property is always set, when the WorkScheduleModel is of type normal_working_time, in contrast when the WorkScheduleModel is of type daily_target_hours it is not set |


## NormalWorkingTimes



| Field | Type | Description |
|-------|------|-------------|
| start | string |  |
| end | string |  |


## WorkingTimeRules



| Field | Type | Description |
|-------|------|-------------|
| id | string |  |
| name | string |  |


## WorkingTime



| Field | Type | Description |
|-------|------|-------------|
| id | string |  |
| start |  |  |
| end |  |  |
| break_time_total_minutes | integer | Total break time in minutes |
| break_times | array |  |
| duration |  |  |
| changed | boolean |  |
| notes | string |  |
| user |  |  |
| working_time_type |  |  |
| working_time_date_span |  |  |
| working_time_request |  |  |
| start_location |  |  |
| end_location |  |  |
| start_platform |  |  |
| end_platform |  |  |
| last_modified |  |  |
| last_modified_by |  |  |
| status |  |  |
| metadata | object |  |


## WorkingTimesPage





## WorkingTimesSortColumn





## WorkingTimeUpdate



| Field | Type | Description |
|-------|------|-------------|
| start |  |  |
| end |  |  |
| break_times | array |  |
| duration_type |  | Must be specified for WorkingTimeTypes with `edit_unit` `days` or `half_days` only |
| changed | boolean |  |
| notes | string |  |
| working_time_type_id | string |  |
| start_location |  |  |
| end_location |  |  |
| status |  |  |
| metadata | object |  |


## WorkingTimeCreate





## DeletedEntryWithMetadata





## DeletedEntryWithMetadataPage





## DeletedEntryWithMetadataSortColumn





## ProjectTimeStatus





## TaskPartial



| Field | Type | Description |
|-------|------|-------------|
| id | string |  |
| name | string |  |
| breadcrumbs | string |  |
| external_id | string |  |


## Task





## TasksPage





## TaskCreate





## TaskUpdate





## TaskBase



| Field | Type | Description |
|-------|------|-------------|
| name | string |  |
| parent_task_id | string | returns the id of the immediate parent task if the task has one. Use this id when creating or a updating a task in order to locate it at the right place in your task tree. |
| external_id | string |  |
| description | string |  |
| description_external | string |  |
| bookable | boolean | when a task is not bookable, no project times can be booked on it. You need to define child tasks, to book on tasks related to this task. |
| billable | boolean |  |
| project_time_notes_required | boolean | depending on this property project times booked on this task have to include notes or not |
| start_date |  | the task is only available for selection after start_date, however, it can change if a lock_date is set and this is after the start_date. Furthermore, no booking of a project time with date < start or > end is possible. |
| end_date |  | the task is only available for selection before end_date, however, it can change if a lock_date is set and this is before the end_date. Furthermore, no booking of a project time with date < start or > end is possible. |
| lock_date |  | with lock_date property you define a point in time before which existing entries can no longer be changed. This way you ensure that

  * existing entries cannot be changed or deleted
  * no entries can be added later
 |
| earliest_start_time |  | set this property to limit the task so that it cannot be booked before this time |
| latest_end_time |  | set this property to limit the task so that it cannot be booked after this time |
| budget_inherited | boolean | when budget is inherited from parent you cannot set it manually. Set this property to false, if you want to change anything in the tasks budget settings |
| budget_planning_type |  |  |
| budget_hours_planned | number | how many hours were planned in the calculation
set budget_hours_planned to make timr calculate budget_planned depending on its budget_planning_type:
  * task_hourly_rate: out of budget_hourly_rate and budget_planned
  * user_hourly_rate: out of fixed hours budget (employee budget) and budget_hours_planned
  * fixed_price: out of budget_hourly_rate and budget_planned
 |
| budget_hourly_rate | number | depending on its budget_planning_type this property may or may not be set:
  * **task_hourly_rate: this property is necessary to calculate budgets, by default it will be set to 0.00**
  * **user_hourly_rate: this property cannot be set**
  * fixed_price: you can set this property if you want to make timr calculate budget_hours_planned or budget_planned based on its value
 |
| budget_planned | number | the price at which the task was sold
set budget_planned to make timr calculate the budget_hours_planned depending on its budget_planning_type:
  * task_hourly_rate: out of budget_hourly_rate and budget_planned
  * user_hourly_rate: out of fixed hours budget (employee budget) and budget_planned
  * fixed_price: out of budget_hourly_rate and budget_planned
 |
| budget_include_non_billable_project_times | boolean | set this property to true, if you want to include not billable hours for all project times booked on this task |
| location_inherited | boolean | set this property to false if you want to set a child task's location explicitly instead of inheriting it from its parent |
| location |  |  |
| location_restriction_radius_meters | integer | set this property to make recording of project times for this task via the app on the smartphone only possible within this defined geofence radius |
| custom_field_1 | string | you can configure custom fields for tasks in the settings of timr under Administration/Settings/Tasks. To add a new custom field, simply choose a name for the field. |
| custom_field_2 | string | you can configure custom fields for tasks in the settings of timr under Administration/Settings/Tasks. To add a new custom field, simply choose a name for the field. |
| custom_field_3 | string | you can configure custom fields for tasks in the settings of timr under Administration/Settings/Tasks. To add a new custom field, simply choose a name for the field. |


## TaskLocation


You can define the location of a task by setting this property. If the task has a parent task, the location is inherited if nothing else is explicitly defined. If you set this property to null, the location will be deleted.



| Field | Type | Description |
|-------|------|-------------|
| lat | number |  |
| lon | number |  |
| address | string |  |
| city | string |  |
| zip_code | string |  |
| state | string |  |
| country | string | the country's international country code |


## TasksSortColumn





## TaskToUserAssignment



| Field | Type | Description |
|-------|------|-------------|
| user |  |  |
| hours_planned | number |  |
| recording_lock |  |  |
| automatically_assigned | boolean |  |


## TaskToUserAssignmentsPage





## TaskToUserAssignmentCreateAndUpdate



| Field | Type | Description |
|-------|------|-------------|
| hours_planned | number |  |
| recording_lock |  |  |


## TaskToUserAssignmentsSortColumn





## RecordingLockType





## BudgetPlanningType


corresponding to the chosen planning type some properties cannot be set:
  * none: no further budget properties can be set
  * user_hourly_rate: budget_hourly_rate cannot be set

for the remaining two types all budget properties are supported





## TaskToLeaderAssignment



| Field | Type | Description |
|-------|------|-------------|
| user |  |  |
| automatically_assigned | boolean |  |


## TaskToLeaderAssignmentsPage





## TaskToLeaderAssignmentsSortColumn





## ProjectTime



| Field | Type | Description |
|-------|------|-------------|
| id | string |  |
| start |  |  |
| end |  |  |
| break_time_total_minutes | integer | Total break time in minutes |
| break_times | array |  |
| duration |  |  |
| changed | boolean |  |
| notes | string |  |
| user |  |  |
| task |  |  |
| billable | boolean |  |
| start_location |  |  |
| end_location |  |  |
| start_platform |  |  |
| end_platform |  |  |
| last_modified |  |  |
| last_modified_by |  |  |
| status |  |  |


## ProjectTimesPage





## ProjectTimesSortColumn





## ProjectTimeUpdate



| Field | Type | Description |
|-------|------|-------------|
| start |  |  |
| end |  |  |
| break_times | array |  |
| changed | boolean |  |
| notes | string |  |
| task_id | string |  |
| billable | boolean |  |
| start_location |  |  |
| end_location |  |  |
| status |  |  |


## ProjectTimeCreate





## DriveLog



| Field | Type | Description |
|-------|------|-------------|
| id | string |  |
| start |  |  |
| end |  |  |
| duration |  |  |
| changed | boolean |  |
| start_mileage | integer |  |
| end_mileage | integer |  |
| distance | integer | Driven distance in kilometers |
| route | string |  |
| purpose | string |  |
| visited | string |  |
| user |  |  |
| car |  |  |
| drive_log_category |  |  |
| start_venue |  |  |
| end_venue |  |  |
| has_track | boolean |  |
| start_location |  |  |
| end_location |  |  |
| start_platform |  |  |
| end_platform |  |  |
| last_modified |  |  |
| last_modified_by |  |  |
| status |  |  |


## DriveLogsPage





## DriveLogsSortColumn





## DriveLogUpdate



| Field | Type | Description |
|-------|------|-------------|
| start |  |  |
| end |  |  |
| changed | boolean |  |
| start_mileage | integer |  |
| end_mileage | integer |  |
| route | string |  |
| purpose | string |  |
| visited | string |  |
| drive_log_category_id | string |  |
| start_location |  |  |
| end_location |  |  |
| status |  |  |


## DriveLogCreate





## CarPartial



| Field | Type | Description |
|-------|------|-------------|
| id | string |  |
| name | string |  |
| plate | string |  |
| external_id | string |  |


## Car





## CarsPage





## CarsSortColumn





## DriveLogCategoryPartial



| Field | Type | Description |
|-------|------|-------------|
| id | string |  |
| name | string |  |
| business | boolean |  |
| color | string |  |


## DriveLogCategory





## DriveLogCategoriesPage





## DriveLogCategoriesSortColumn





## VenuePartial



| Field | Type | Description |
|-------|------|-------------|
| id | string |  |
| name | string |  |
| city | string |  |
| zip_code | string |  |
| street | string |  |
| street_number | string |  |
| country | string |  |
| lat | number |  |
| lon | number |  |


## Track





## Waypoint



| Field | Type | Description |
|-------|------|-------------|
| lat | number |  |
| lon | number |  |


## DriveLogStatus





## WorkingTimeRequestStatus





## WorkingTimeRequestPartial


References a request if the working time is part of one.  A working time can either be part of a working time request or a working time date span, never both.



| Field | Type | Description |
|-------|------|-------------|
| id | string |  |


## WorkingTimeRequest



| Field | Type | Description |
|-------|------|-------------|
| id | string |  |
| start |  |  |
| start_half_day | boolean |  |
| end |  |  |
| end_half_day | boolean |  |
| notes | string |  |
| user |  |  |
| working_time_type |  |  |
| created |  |  |
| last_modified |  |  |
| last_modified_by |  |  |
| status_comment | string |  |
| status |  |  |


## WorkingTimeRequestsPage





## WorkingTimeRequestsSortColumn





## DeletedEntryPartial



| Field | Type | Description |
|-------|------|-------------|
| id | string |  |
| last_modified |  |  |
| last_modified_by |  |  |


## DeletedEntryPage





## DeletedEntrySortColumn





## WorkingTimeDateSpanPartial


References a date span if the working time is part of one.  A working time can either be part of a working time date span or a request, never both.



| Field | Type | Description |
|-------|------|-------------|
| id | string |  |


## WorkingTimeDateSpan



| Field | Type | Description |
|-------|------|-------------|
| id | string |  |
| start |  |  |
| start_half_day | boolean |  |
| end |  |  |
| end_half_day | boolean |  |
| notes | string |  |
| user |  |  |
| working_time_type |  |  |
| last_modified |  |  |
| last_modified_by |  |  |
| metadata | object |  |


## WorkingTimeDateSpanPage





## WorkingTimeDateSpansSortColumn





## WorkingTimeDateSpanUpdate



| Field | Type | Description |
|-------|------|-------------|
| start |  |  |
| start_half_day | boolean |  |
| end |  |  |
| end_half_day | boolean |  |
| notes | string |  |
| working_time_type_id | string |  |
| metadata | object |  |


## WorkingTimeDateSpanCreate





## WorkingTimeTypePartial



| Field | Type | Description |
|-------|------|-------------|
| id | string |  |
| name | string |  |
| external_id | string |  |


## WorkingTimeType



| Field | Type | Description |
|-------|------|-------------|
| id | string |  |
| name | string |  |
| short_name | string |  |
| description | string |  |
| external_id | string |  |
| edit_unit |  |  |
| category |  |  |
| sub_category |  |  |
| recording_mode_user |  |  |
| non_creditable_deductible | number |  |
| compensation_deductible | number |  |
| archived | boolean |  |


## DurationUnit





## WorkingTimeTypeCategory





## WorkingTimeTypeSubCategory





## RecordingModeUser





## WorkingTimeTypesPage





## WorkingTimeTypesSortColumn





## PagingInformation



| Field | Type | Description |
|-------|------|-------------|
| next_page_token | string |  |


## SortDirection



