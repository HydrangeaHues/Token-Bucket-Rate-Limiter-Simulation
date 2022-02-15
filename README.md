# Token-Bucket-Rate-Limiter-Simulation
A multi-threaded implementation of the Token Bucket rate limiting algorithm using Python.

## Functionality
The program will ask the user for two inputs, a max token count and a refill rate (with units of seconds), which will be applied to the first token bucket created. A second token bucket will be created automatically with a max token count of 5 and a refill rate of 10 seconds. This second bucket exists to prove the program works when dealing with multiple token buckets, as well as to showcase what happens when a bucket uses tokens more quickly than they can be replaced. The program simulates making requests to both buckets for 60 seconds, sleeping for 3 seconds before the next requests are sent. When a request is made to a bucket, the program will print out the name of the thread making the request, the bucket processing the request, the number of tokens present in the bucket, and whether or not the request was successful. If the request was dropped, the printed output will mention how long the user must wait until being able to successfully request again (effectively printing the refresh rate of the bucket)

## Technology
### Programming Language
Python was used for this project mainly because I am picking the language back up again and wanted to use it. Due to the project dealing with concurrency in the form of threading, I believe other languages (such as Go) would be better suited for designing rate limiters in a production environment, but Python worked for my case.

### Rate Limiting Algorithms
There are many different rate limiting algorithms, each with pros and cons, which I will briefly cover here just for background information.
- Token Bucket (used in this project)
  - Tokens are added to a bucket at some rate. When a request comes, if the bucket has sufficient tokens to process the request, the request is allowed. Otherwise, it is rejected.
  - Pros: Memory efficient and can accurately allow bursts of traffic.
  - Cons: Potentially hard to tune the max token count and refill rate for the best performance for your use case.
- Leaking Bucket
  - Requests are placed in a queue of finite size and processed at a fixed rate. If a request comes and the queue is full, the request is rejected, otherwise it is added to the queue (accepted).
  - Pros: Memory efficient and can provide stable output of requests if that is desired.
  - Cons: Potentially hard to tune to get the best performance for your use case, and a burst of traffic could cause new requests to continually be dropped while old requests are processed.
- Fixed Window Counter
  - A timeline is split into fixed size windows. Every request received within a window increments the counter for that window, and once the counter hits a predefined limit, every request afterwards is dropped. 
  - Pros: Memory efficient.
  - Cons: Cannot accurately limit requests if a burst of requests come at the second half of one window, and the first half of the next.
- Sliding Window Log
  - A window of fixed size slides along the timeline, recording the timestamp of each request that comes in in a log. Each time a new request comes in, discard the timestamps of requests that are outside the current time window. If the number of timestamps in the log is less than a predefined limit, allow the new request.
  - Pros: Accurate rate limiting.
  - Cons: Uses a lot of memory compared to the other algorithms.
- Sliding Window Counter
  - A hybrid of Fixed Window Counter and Sliding Window Log, this algorithm splits a timeline into fixed windows while also having a sliding window that moves along the timeline. Calculate the number of requests in the sliding window by using the following formula: # Requests in Current Fixed Window + # Requests in Previous Fixed Window * % of the sliding window is still covering the previous fixed window.
  - Pros: Traffic is smoothed out due to the rate being based on average.
  - Cons: The rate limiting is approximate, so potentially not good if you need super strict / accurate rate limiting.


## Places for Expansion / Improvement
- Handling rejected requests
  -  An important part of a production rate limiter that I did not implement here is a robust and helpful way of handling rejected requests. In the event a user's request is denied due to rate limiting, it would be best to provide them a detailed error message and potentially hold onto their rejected request to try it again for them. This program drops the rejected requests entirely without attempting to retry even once, which is likely not a best practice for a production envrionment.
- Allow more expensive requests to cost more tokens
  - Currently every allowed request subtracts a single token from the bucket, but in reality some requests may be more costly and thus we would want to have them use more tokens than other requests.
- Error handling surrounding creating accounts / user input
  - There is nothing stopping a user from creating an account with an ID that is already taken, which would effectively override the existing account. Also, there is nothing checking user input to ensure they are reasonable values. That was not the focus of this project for me, but handling / checking of that manner should be done in a production envrionment.
- Allow for dynamically creating / destroying accounts
  - Currently the program is locked to having only 2 buckets being requested, as I just wanted to showcase the algorithm at work. If this were an actual rate limiter in production, we would need to be able to add / remove accounts more freely.
- Use a language that is better with concurrency
