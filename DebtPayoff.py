import math
import pandas as pd
import sqlite3

class DebtPayoffSchedule:

    global db
    db = sqlite3.connect('Data.db')
    
    def __init__(self, spreadsheet, usage, payoffTerm):
        self.spreadsheet = spreadsheet
        self.creditUsage = usage
        self.payoffTerm = payoffTerm
        self.df = pd.read_excel(spreadsheet, sheet_name = ["Credit Card Data", "Loan Data"])

    def driver(self):
        self.writeDatabase()
        self.payOrderCards(self.creditUsage)
        self.payOrderLoans(self.payoffTerm)
        self.outputData()


    def writeDatabase(self):

        #writes initial data to database
        for sheet in self.df:
            self.df[sheet].to_sql(sheet, db, index = False)
        db.commit()

    def payOrderCards(self, creditUsage):
        #grab data
        if int(creditUsage) >= 100 or int(creditUsage) < 0:
            return print("Credit usage is out of bounds. Please enter a value between 0-99")

        df = self.df.get("Credit Card Data")

        #calculates interest based on current balance
        interest = df['Current Balance'] * df['Interest Rate']

        #add interest to current balance
        wInterest = df['Current Balance'] + interest

        #finds min val required to bring credit usage to n%
        belowUsage = df['Max Credit'] * (int (creditUsage)/100)

        #finds min payment required to bring to below usage
        df['Minimum Payment'] = minPay = wInterest - belowUsage
        df['Paid Off (Minimum Payments)'] = minPay
        df['Percent of Debt (Minimum Payments)'] = minPay/wInterest * 100
        sumMinPayment = minPay.sum()


        #how much balance is left after minimum payments
        df['Current Balance (Minimum Payments)'] = wInterest - minPay

        #use interest to calculate priority for weighted payments
        #higher interest accumulating cards are paid off first
        #sumMinPayment is still the required num to keep below n%
        #add new tables to original dataframe so we can easily manipulate data

        df["Interest Accrued"] = interest
        df["With Interest"] = wInterest
        df["Original Balance"] = df['Current Balance']
        df["Paid Off (Weighted Payments)"] = [0 for i in range(wInterest.size)]
        df["Percent of Debt"] = [0 for i in range(wInterest.size)]
        df = df.sort_values(by = "Interest Accrued", ascending=False)
        df["Priority"] = [i+1 for i in range(wInterest.size)]

        i = 0
        rem = sumMinPayment
        while rem >= 0:
            if rem - df.loc[i, 'With Interest'] < 0:
                df.loc[i, "Paid Off (Weighted Payments)"] = rem
                df.loc[i, "Percent of Debt"] = rem / df.loc[i, 'With Interest'] * 100
                df.loc[i, "Current Balance"] = df.loc[i, 'With Interest'] - rem
                break
            else:
                rem = sumMinPayment - df.loc[i, 'With Interest']
                sumMinPayment -= rem
                df.loc[i, 'Current Balance'] = 0
                df.loc[i, "Percent of Debt"] = sumMinPayment / df.loc[i, "With Interest"] * 100
                df.loc[i, "Paid Off (Weighted Payments)"] = sumMinPayment
            i += 1

        df['Weighted Payment'] = df['Paid Off (Weighted Payments)']

        #manipulate dataframe to prepare for output to database
        df = df.drop(columns = ['With Interest', 'Interest Accrued'])
        df = df.round({'Paid Off (Weighted Payments)': 2, 'Percent of Debt' : 2, 'With Interest': 3, "Percent of Debt (Minimum Payments)": 2})
        df = df.rename(columns = {'Current Balance': "Current Balance (Weighted Payments)", "Percent of Debt": "Percent of Debt (Weighted)"})

        column = ['Minimum Payment', 'Weighted Payment', 'Original Balance', 'Current Balance (Weighted Payments)', 'Current Balance (Minimum Payments)', 'Paid Off (Weighted Payments)', 'Paid Off (Minimum Payments)'
        , 'Percent of Debt (Weighted)', "Percent of Debt (Minimum Payments)",  'Interest Rate', 'Description', 'Priority']
        df = df.reindex(columns = column)
        df.to_sql('Credit Card Data', db, if_exists = 'replace', index = False)

        db.commit()
    
    def payOrderLoans(self, payoffTerm):
        if int(payoffTerm) <= 0 or int(payoffTerm) > 600:
            return print("Payment terms out of bounds. Please use a number 1-600")

        df = self.df.get("Loan Data")
        
        #using the amortization formula, we can calulate monthly payments using the information we get from the dataframe
        principal = df['Current Balance']
        rate = df['Interest Rate']
        totalPayments = int (payoffTerm)

        monthlyPayments = principal * ((rate * ((1 + rate)** totalPayments)) / (((1 + rate) ** totalPayments) - 1))

        #use monthly payments and compound interest to calculate the balance the loan after each month
        remBalance = [i for i in range(int (payoffTerm))]
        initial = principal + principal * rate
        remBalance[0] = principal.sum()

        #fills remBalance to be used later in df2
        for i in range(int (payoffTerm) + 1):
            sum = initial - monthlyPayments
            if sum.sum() < 0:
                break
            else:
                remBalance[i] = round(sum.sum(), 2)
            
            initial = initial - monthlyPayments
            initial += initial * rate

        #adding to dataframe to make it easier to transfer to database
        df['Monthly Payments (Weighted)'] = monthlyPayments
        df = df.sort_values(by = "Monthly Payments (Weighted)", ascending= False)
        df['Priority'] = [i+1 for i in range(monthlyPayments.size)]

        #slight data cleaning
        df = df.round({'Monthly Payments (Weighted)':2})
        df.to_sql('Loan Data', db, if_exists = 'replace', index = False)

        #use a separate table for current loan balance after n months
        sumPayments = round(monthlyPayments.sum(), 2)
        minPayment = [sumPayments for i in range(int (payoffTerm))]

        d = {'Remaining Balance': remBalance, 'Monthly Payments (Minimum)' : minPayment}
        df2 = pd.DataFrame(data = d)
        df2['Percent of Loan'] = df2['Monthly Payments (Minimum)']/df2['Remaining Balance'] * 100
        df2 = df2.round({'Percent of Loan': 2})
        df2['Terms Completed'] = [i+1 for i in range(int (payoffTerm))]

        df2.to_sql('Loan Payoff Schedule', db, if_exists = 'replace', index = False)

        db.commit()


    def outputData(self):
        #since we've organized data in the methods for card and loan data, we just use this method to close the database
        db.close()

spreadsheet = input("Enter spreadsheet name: ")
usage = input("Enter credit usage: ")
payoffTerm = input("Enter payoff term: ")

if spreadsheet.isalpha and usage.isdigit and payoffTerm.isdigit:
    p = DebtPayoffSchedule(spreadsheet, usage, payoffTerm)
    p.driver()
else:
    print("Please insert correct datatypes.")
    
