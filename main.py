import time
import threading

class RequestTokenBucket(object):
    """
    A class that models a token bucket to be used for rate limiting purposes.

    Attributes
    ----------
    maxTokens : int
        The maximum number of tokens the RequestTokenBucket object is able to hold at any given time.
        Defaults to 10.
    refillRate : int
        The number of seconds it takes for a single token to be refilled into the RequestTokenBucket object.
        Defaults to 5.
    lastRequestTimestamp : int
        A timestamp of the last time a request was allowed by the bucket, represented as seconds since epoch.
    currentCount : int
        The current number of tokens in the bucket.
    lock : Lock
        A Lock object that allows the bucket to be locked when multiple threads might be trying to make requests.

    Methods
    -------
    calculateCurrentTokens():
        Determine the number of tokens a RequestTokenBucket object should have and set the object's currentCount attribute to that value.
        Return without setting the currentCount value if the RequestTokenBucket object does not have a lastRequestTimestamp value, as
        we assume this to mean no requests have been made to the bucket yet, and buckets are full of tokens when instantiated.
    
    printBucketSummary():
        Print a formatted summary of the max token capacity, refill rate, current token count, and last request time of a RequestTokenBucket object.
    """

    def __init__(self, maxTokens=10, refillRate=5):
        """
        Constructor for RequestTokenBucket objects.
        Initialize the lastRequestTimestamp attribute as None because we could not have made a request to a bucket that did not exist before.
        Initialize the currentCount attribute to the value of maxTokens, as we want the RequestTokenBucket object to be full when instantiated.

        Parameters
        ----------
        maxTokens : int
            The maximum number of tokens the RequestTokenBucket object is able to hold at any given time.
            Defaults to 10.
        refillRate : int
            The number of seconds it takes for a single token to be refilled into the RequestTokenBucket object.
            Defaults to 5.
        """
        self.maxTokens = maxTokens
        self.refillRate = refillRate
        self.lastRequestTimestamp = None
        self.currentCount = maxTokens
        self.lock = threading.Lock()

    def calculateCurrentTokens(self):
        """
        Determine the number of tokens a RequestTokenBucket object should have and set the object's currentCount attribute to that value.
        Return without setting the currentCount value if the RequestTokenBucket object does not have a lastRequestTimestamp value, as
        we assume this to mean no requests have been made to the bucket yet, and buckets are full of tokens when instantiated.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        if self.lastRequestTimestamp is None:
            return
        tokensSinceLastRequest = self.__timeSinceLastRequest() // self.refillRate
        self.currentCount = min(self.maxTokens, self.currentCount + tokensSinceLastRequest)
    
    def printBucketSummary(self):
        """
        Print a formatted summary of the max token capacity, refill rate, current token count, and last request time of a RequestTokenBucket object.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        print("Max Token Capacity: {}".format(self.maxTokens))
        print("Refill Rate: {}".format(self.refillRate))
        print("Current Token Count: {}".format(self.currentCount))
        print("Last Request Time: {}".format(self.lastRequestTimestamp))

    @classmethod
    def __getCurrentTimeInSeconds(cls):
        """
        Return the current time represented in seconds since epoch.

        Parameters
        ----------
        None

        Returns
        -------
        An integer representing the current time as seconds since epoch.
        """
        return int(round(time.time()))
    
    def __timeSinceLastRequest(self):
        """
        Return an integer representing the number of seconds since the last request made to a RequestTokenBucket object.

        Parameters
        ----------
        None

        Returns
        -------
        An integer representing the number of seconds since the last request made to a RequestTokenBucket object.
        """
        return self.__getCurrentTimeInSeconds() - self.lastRequestTimestamp
    

class TokenBucketRateLimiter(object):
    """
    A class that interacts with the RequestTokenBucket class to simulate rate limiting behavior. 

    Attributes
    ----------
    rateLimiterDict : Dictionary
        A dictionary that maps an account ID (key) to a RequestTokenBucket object (value).

    Methods
    -------
    addAccount(accountID, requestTokenBucket):
        Add the accountID and requestTokenBucket as a key-value pair to the TokenBucketRateLimiter object's rateLimiterDict.

    
    removeAccount(accountID):
        Remove the account identified by accountID from the TokenBucketRateLimiter object's rateLimiterDict.

    
    allowRequestToService(accountID):
        Determine if a request should be allowed based on the current token count of a bucket.
        Print information about the bucket being requested and if the request will be allowed.
        If allowed, perform the request in a thread-safe manner.
    """

    def __init__(self):
        """
        Constructor for TokenBucketRateLimiter objects.

        Parameters
        ----------
        None
        """
        self.ratelimiterDict = {}

    def addAccount(self, accountID, requestTokenBucket):
        """
        Add the accountID and requestTokenBucket as a key-value pair to the TokenBucketRateLimiter object's rateLimiterDict.

        Parameters
        ----------
        accountID : int
            The ID of the account we are working with.
        requestTokenBucket : RequestTokenBucket
            The token bucket we want to use to determine if requests from the account associated with accountID should be allowed or not.

        Returns
        -------
        None
        """
        self.ratelimiterDict[accountID] = requestTokenBucket
    
    def removeAccount(self, accountID):
        """
        Remove the account identified by accountID from the TokenBucketRateLimiter object's rateLimiterDict.

        Parameters
        ----------
        accountID : int
            The ID of the account we are working with.

        Returns
        -------
        None
        """
        del self.ratelimiterDict[accountID]

    def allowRequestToService(self, accountID):
        """
        Calculate the current number of tokens in the bucket associated with accountID, allow the request if there are enough tokens to do so, reject the request if not.
        Print information regarding which thread is making a request, which bucket they are requesting, and the current token count of the bucket being requested.

        Parameters
        ----------
        accountID : int
            The ID of the account we are working with.

        Returns
        -------
        A boolean denoting if the request was allowed or not.
        """
        tokenBucket = self.ratelimiterDict[accountID]
        # Lock the bucket so that we do not have concurrency issues that result in us bypassing the rate limit.
        with tokenBucket.lock:
            tokenBucket.calculateCurrentTokens()
            print("**** {} is making a request to bucket {}****".format(threading.current_thread().name, accountID))
            print("Current Tokens for Bucket {}: {}".format(accountID, tokenBucket.currentCount))
            # Allow the request if the token bucket has at least 1 token.
            # If the request is allowed, we will update the bucket's lastRequestTimestamp and remove a token from the bucket.
            if tokenBucket.currentCount > 0:
                print("Processing request\n")
                tokenBucket.lastRequestTimestamp = int(round(time.time()))
                tokenBucket.currentCount -= 1
                return True
            else:
                print("Not enough tokens to process request. Please try again in {} seconds.\n".format(tokenBucket.refillRate))
        return False
        

def simulateRequests(rateLimiter):
    """
    Takes in a TokenBucketRateLimiter object and simulates making requests to buckets within that object for 60 seconds.

    Parameters
    ----------
    rateLimiter : TokenBucketRateLimiter
        A TokenBucketRateLimiter containing buckets we want to simulate the rate limiting capabilities of.

    Returns
    -------
    None
    """
    end_time = time.time() + 60
    while time.time() < end_time:
        rateLimiter.allowRequestToService(1)
        rateLimiter.allowRequestToService(2)
        time.sleep(3)

rateLimiter = TokenBucketRateLimiter()

maxTokensInput = int(input("Please specify the maximum number of tokens the first bucket should have: "))
refillRateInput = int(input("Please specify the rate in seconds at which a single token should be refilled into the first bucket: "))

rateLimiter.addAccount(1, RequestTokenBucket(maxTokensInput, refillRateInput))
print("**** Summary of Specs for Token Bucket One ****")
rateLimiter.ratelimiterDict[1].printBucketSummary()
print("\n")

rateLimiter.addAccount(2, RequestTokenBucket(5, 10))
print("**** Summary of Specs for Token Bucket Two ****")
rateLimiter.ratelimiterDict[2].printBucketSummary()
print("\n")

if __name__=="__main__":
    thread1 = threading.Thread(target=simulateRequests, args=(rateLimiter,))
    thread2 = threading.Thread(target=simulateRequests, args=(rateLimiter,))
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()
    print("End")
