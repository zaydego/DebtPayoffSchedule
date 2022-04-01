Isaiah Jones, 3/3/2022

Methods:
-driver()
    -gathers input from user and calls all other methods
-writeDatabase()
    -writes the initial excel doc to database
-payOrderCards()
    -takes credit usage a parameter
    -uses dataframe to calculate monthly payments, both weighted and unweighted
    -weighted payments are derived from the minimum payment required to keep total utilization under n%. this minimum payment is then distributed across
    cards in priority order. priority is determined by which card accrues the most interest that month
    -minimum unweighted payments are calculated using dataframe
    -data is then organized according to requested output and then committed to the database
-payOrderLoans()
    -takes payoff terms as a parameter
    -calculates required weighted monthly payments per loan by applying the amorization formula to the dataframe
    -unweighted min payment is the sum of weighted min payments
    -this data is organized into a single dataframe
    -for calculating percent relative to current balance, a second dataframe is created and allocated a separate table in the database
        - this dataframe uses a list remBalance[] where remBalance[i] is the current balance remaining on the ith month before payment
        - percent is calculated by manipulating this dataframe
        - the column Remaining Balance in this dataframe is the value before adding interest!
    -data is organized then output to database as requested, 
-outputData()
    -used to close database connection since data is cleaned and organized in its appropiate method

Concerns & Possible Issues:
-The program does work as intended. However, I wasn't sure how to test for vulnerabilities.
I tried to make sure the parameters were appropiate for credit usage and payoff terms.
-Hopefully I calculated the min/weighted payments as you intended.
-Certain values in the database were rounded for easy reading and appropiate terms. These values weren't rounded until after calculations.