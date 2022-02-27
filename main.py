import time
import threading

class RequestTokenBucket(object):
    """
    A class that models a token bucket to be used for rate limiting purposes.

    Attributes
    ----------
    max_tokens : int
        The maximum number of tokens the RequestTokenBucket object is able to hold at any given time.
        Defaults to 10.
    refill_rate : int
        The number of seconds it takes for a single token to be refilled into the RequestTokenBucket object.
        Defaults to 5.
    last_request_timestamp : int
        A timestamp of the last time a request was allowed by the bucket, represented as seconds since epoch.
    current_count : int
        The current number of tokens in the bucket.
    lock : Lock
        A Lock object that allows the bucket to be locked when multiple threads might be trying to make requests.

    Methods
    -------
    calculate_current_tokens():
        Determine the number of tokens a RequestTokenBucket object should have and set the object's current_count attribute to that value.
        Return without setting the current_count value if the RequestTokenBucket object does not have a last_request_timestamp value, as
        we assume this to mean no requests have been made to the bucket yet, and buckets are full of tokens when instantiated.
    
    print_bucket_summary():
        Print a formatted summary of the max token capacity, refill rate, current token count, and last request time of a RequestTokenBucket object.
    """

    def __init__(self, max_tokens=10, refill_rate=5):
        """
        Constructor for RequestTokenBucket objects.
        Initialize the last_request_timestamp attribute as None because we could not have made a request to a bucket that did not exist before.
        Initialize the current_count attribute to the value of max_tokens, as we want the RequestTokenBucket object to be full when instantiated.

        Parameters
        ----------
        max_tokens : int
            The maximum number of tokens the RequestTokenBucket object is able to hold at any given time.
            Defaults to 10.
        refill_rate : int
            The number of seconds it takes for a single token to be refilled into the RequestTokenBucket object.
            Defaults to 5.
        """
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self.last_request_timestamp = None
        self.current_count = max_tokens
        self.lock = threading.Lock()

    def calculate_current_tokens(self):
        """
        Determine the number of tokens a RequestTokenBucket object should have and set the object's current_count attribute to that value.
        Return without setting the current_count value if the RequestTokenBucket object does not have a last_request_timestamp value, as
        we assume this to mean no requests have been made to the bucket yet, and buckets are full of tokens when instantiated.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        if self.last_request_timestamp is None:
            return
        tokens_since_last_request = self.__time_since_last_request() // self.refill_rate
        self.current_count = min(self.max_tokens, self.current_count + tokens_since_last_request)
    
    def print_bucket_summary(self):
        """
        Print a formatted summary of the max token capacity, refill rate, current token count, and last request time of a RequestTokenBucket object.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        print("Max Token Capacity: {}".format(self.max_tokens))
        print("Refill Rate: {}".format(self.refill_rate))
        print("Current Token Count: {}".format(self.current_count))
        print("Last Request Time: {}".format(self.last_request_timestamp))

    @classmethod
    def __get_current_time_in_seconds(cls):
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
    
    def __time_since_last_request(self):
        """
        Return an integer representing the number of seconds since the last request made to a RequestTokenBucket object.

        Parameters
        ----------
        None

        Returns
        -------
        An integer representing the number of seconds since the last request made to a RequestTokenBucket object.
        """
        return self.__get_current_time_in_seconds() - self.last_request_timestamp
    

class TokenBucketRateLimiter(object):
    """
    A class that interacts with the RequestTokenBucket class to simulate rate limiting behavior. 

    Attributes
    ----------
    rate_limiter_dict : Dictionary
        A dictionary that maps an account ID (key) to a RequestTokenBucket object (value).

    Methods
    -------
    add_account(account_id, request_token_bucket):
        Add the account_id and request_token_bucket as a key-value pair to the TokenBucketRateLimiter object's rate_limiter_dict.

    
    allow_request_to_service(account_id):
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
        self.rate_limiter_dict = {}

    def add_account(self, account_id, request_token_bucket):
        """
        Add the account_id and request_token_bucket as a key-value pair to the TokenBucketRateLimiter object's rate_limiter_dict.

        Parameters
        ----------
        account_id : int
            The ID of the account we are working with.
        request_token_bucket : RequestTokenBucket
            The token bucket we want to use to determine if requests from the account associated with account_id should be allowed or not.

        Returns
        -------
        None
        """
        self.rate_limiter_dict[account_id] = request_token_bucket

    def allow_request_to_service(self, account_id):
        """
        Calculate the current number of tokens in the bucket associated with account_id, allow the request if there are enough tokens to do so, reject the request if not.
        Print information regarding which thread is making a request, which bucket they are requesting, and the current token count of the bucket being requested.

        Parameters
        ----------
        account_id : int
            The ID of the account we are working with.

        Returns
        -------
        A boolean denoting if the request was allowed or not.
        """
        token_bucket = self.rate_limiter_dict[account_id]
        # Lock the bucket so that we do not have concurrency issues that result in us bypassing the rate limit.
        with token_bucket.lock:
            token_bucket.calculate_current_tokens()
            print("**** {} is making a request to bucket {}****".format(threading.current_thread().name, account_id))
            print("Current Tokens for Bucket {}: {}".format(account_id, token_bucket.current_count))
            # Allow the request if the token bucket has at least 1 token.
            # If the request is allowed, we will update the bucket's last_request_timestamp and remove a token from the bucket.
            if token_bucket.current_count > 0:
                print("Processing request\n")
                token_bucket.last_request_timestamp = int(round(time.time()))
                token_bucket.current_count -= 1
                return True
            else:
                print("Not enough tokens to process request. Please try again in {} seconds.\n".format(token_bucket.refill_rate))
        return False
        

def simulate_requests(rate_limiter):
    """
    Takes in a TokenBucketRateLimiter object and simulates making requests to buckets within that object for 60 seconds.

    Parameters
    ----------
    rate_limiter : TokenBucketRateLimiter
        A TokenBucketRateLimiter containing buckets we want to simulate the rate limiting capabilities of.

    Returns
    -------
    None
    """
    end_time = time.time() + 60
    while time.time() < end_time:
        rate_limiter.allow_request_to_service(1)
        rate_limiter.allow_request_to_service(2)
        time.sleep(3)

rate_limiter = TokenBucketRateLimiter()

max_tokens_input = int(input("Please specify the maximum number of tokens the first bucket should have: "))
refill_rate_input = int(input("Please specify the rate in seconds at which a single token should be refilled into the first bucket: "))

rate_limiter.add_account(1, RequestTokenBucket(max_tokens_input, refill_rate_input))
print("**** Summary of Specs for Token Bucket One ****")
rate_limiter.rate_limiter_dict[1].print_bucket_summary()
print("\n")

rate_limiter.add_account(2, RequestTokenBucket(5, 10))
print("**** Summary of Specs for Token Bucket Two ****")
rate_limiter.rate_limiter_dict[2].print_bucket_summary()
print("\n")

if __name__=="__main__":
    thread1 = threading.Thread(target=simulate_requests, args=(rate_limiter,))
    thread2 = threading.Thread(target=simulate_requests, args=(rate_limiter,))
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()
    print("End")
