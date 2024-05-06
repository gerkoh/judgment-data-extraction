import anthropic
import os
from dotenv import load_dotenv
import json
import time
import csv

load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

client = anthropic.Anthropic()
client.api_key = ANTHROPIC_API_KEY

def get_full_text_from_judgment(file_path):
    with open(file_path, 'r', encoding="utf-8") as file:
        data = json.load(file)
        full_text = data["full_text"]
    return full_text

def claude3_api_call(judgment_full_text):
    response = anthropic.Anthropic().messages.create(
        model="claude-3-opus-20240229",
        system="Output in JSON. You are a Family Law Legal Expert and you can understand text in English (United Kingdom). This information you extract is very important, as no one else is checking your information, if you get it wrong, children are going to suffer. Focus on the division of matrimonial assets and you are focusing on the values that the Judge decides on. Take the judgment and extract the required information from it. ",
        max_tokens=2000,
        messages=[
            {
                "role": "user",
                "content": 
                    "Hello world"
                    f"""
                    Extract data from the judgment according to the fixed headers given. Follow the output format strictly. Pay close attention to the context of the judgment to accurately determine each value decided by the Judge. If any information is not explicitly stated, use logical reasoning based on the given data to provide a calculated or estimated response.\n
                    - Summary: <A summary of all the information that you had used to produce the outputs below>\n
                    - Length of marriage till Interim Judgment for divorce (including separation period): <Extract length of marriage as an integer. Otherwise, determine based on the context what is the "Date of marriage" which is the date that the husband and wife was married on. Also based on the context the "Date of Interim Judgment" which is also known as the date that Interim Judgment was granted. After determining the value for "Date of marriage" and "Date of Interim Judgment", subtract the "Date of marriage" from the "Date of Interim Judgment" ; if decimal place is more than 0.5, round it up to the nearest integer. Else round down to nearest integer.>\n
                    - Length of marriage (exclude separation period): <Extract length of marriage as an integer. Otherwise, determine based on the context what is the "Date of marriage" which is the date that the husband and wife was married on. Also based on the context the "Date of separation" which is also known as the date or year that the husband and wife was no longer staying together, if the text only provides the year, you can assume it is 1st Jan of that year. After determining the value for "Date of marriage" and "Date of separation", subtract the "Date of marriage" from the "Date of separation" ; if decimal place is more than 0.5, round it up to the nearest integer. Else round down to nearest integer.>\n
                    - Number of children: <Extract the exact number of children mentioned in the judgment, in integer>\n
                    - Wife's income (monthly): <Determine based on the context what is the wife's income in integer, if wife is a "homemaker" or "retired" and clearly "unemployed", enter the integer "0". If undisclosed, enter "Undisclosed">\n
                    - Husband's income (monthly): <if judgment contains the information, then provide the extracted data as an integer. If undisclosed, enter "Undisclosed">\n
                    - Single or dual income marriage: <Determine based on the context whether it was a 'single' or 'dual' income marriage. If undisclosed, enter 'Undisclosed'>\n
                    - Direct contribution (Wife): <Extract the integer attributed to the Wife's direct contribution; choose the appropriate value based on the context>\n
                    - Indirect contribution (Wife): <Extract the integer attributed to the Wife's indirect contribution; choose the appropriate value based on the context>\n
                    - Average ratio (Wife): <Extract the integer attributed to the Wife's average ratio; choose the appropriate value based on the context. Otherwise, calculate the average of direct and indirect contributions to get the average ratio for the wife>\n
                    - Final ratio (post-adjustments): <Extract the final ratio after adjustments are made>\n
                    - Adjustments: <Calculate the difference between the average ratio and the final ratio and describe it as a positive or negative value>\n
                    - Adjustments were for: <Extract the specific reasons given in the judgment for the adjustments, else "">\n
                    \n
                    Sample input 0: Husband and Wife married on 9 September 2001. Divorce was filed on 8 September 2023. Interim Judgment was granted on 1 April 2024. Husband and Wife has been married for about 21 years until it broke down. During the marriage, they have 3 children - 2 boys and 1 girl. The Wife was a homemaker during the large majority of the marriage. The Husband earned an income of $11,408.50. We accepted the argument that the correct ratio for the parties' direct contribution was 70:30 in the wife’s favour and not 75:25.  In relation to the children, the Father has assumed their care in a substantial way since 11 June 2015, with major adjustments to his work hours. There was, additionally, evidence from his former colleagues to show that, when he was with his previous employer, Bank B, he avoided working or travelling on weekends and in fact requested for permission to stop travelling altogether for a period of time to care for the children and provide relief to the Mother during her depression in 2011. Taking a broad brush approach, I am of the view that a 60:40 assessment of indirect contributions in favour of the wife would be fair. The Judge divided the pool of assets equally. Since that will result in a ratio of 103:97 which deviates only slightly from the equal division that the Judge ordered, we will not interfere with her decision on this point.\n
                    \n
                    Sample output 0:\n
                    "Length of marriage till Interim Judgment for divorce (including separation period)": 23\n
                    "Length of marriage (exclude separation period)": 21\n
                    "Number of children": 3\n
                    "Wife's income (monthly)": 0\n
                    "Husband's income (monthly)": 11408.50\n
                    "Single or dual income marriage": Single\n
                    "Direct contribution (Wife)": 70\n
                    "Indirect contribution (Wife)": 60\n
                    "Average ratio (Wife)": 65\n
                    "Final ratio (post-adjustments)": 50\n
                    "Adjustments": Minus 15\n
                    "Adjustments were for": Undisclosed\n
                    \n
                    Sample input 1: We uphold the Judge’s assessment of the ratio of indirect contributions as 60:40 in the wife’s favour. That leaves the sum of INR 4.8m which, according to the Wife, constituted a loan that the Husband advanced to his father in three tranches between 2013 and 2017. Counsel for the Wife submits that the DJ erred in failing to add this sum to the matrimonial pool despite noting that there were “significant gaps” in the Husband’s evidence as to how he had expended it. I agree that the Husband had been less than forthcoming in disclosing the nature and whereabouts of the INR 4.8m. I note, however, that the DJ had already expressly accounted for the inconsistencies in the Husband’s evidence by adjusting the final apportionment of assets between the Husband and Wife from 61.88 (Husband): 38.11 (Wife) to 58 (Husband) : 42 (Wife) (see GD at [51]). In view of this adjustment, I do not find it necessary or appropriate to add the sum of INR 4.8m to the matrimonial pool. 
                    \n
                    Sample output 1:\n
                    "Indirect contribution (Wife)": 60\n
                    "Adjustments were for": DJ had taken into account the inconsistencies in the Husband's evidence\n
                    \n
                    Sample input 2: Nevertheless, I decline to draw an adverse inference against either party as I find that there is no substratum of evidence that establishes a prima facie case against the other party that there are remaining assets which have not been disclosed to the court (see Koh Bee Choo v Choo Chai Huah [2007] SGCA 21 at [28]). To the extent that any funds in the Husband’s UOB One Account and POSB Accounts had not been disclosed previously, they have now been included in the pool of matrimonial assets (see [43] above). As for the unexplained withdrawals of sums such as $25,000 and $9,000 by the Husband in 2015, I am of the view that the size and timing of these withdrawals are not such that they disclose a prima facie case of dissipation. As for the Wife’s claim that the Husband has not been forthcoming about his sources of funds and has deliberately understated his income, I find that this is more relevant to the issue of maintenance which is discussed below.\n
                    \n
                    Sample output 2:\n
                    "Adjustments were for": Judge found both parties had failed to provide full and frank disclosure to some extent, but declined to draw adverse inference against either party.\n
                    \n
                    Sample input 3: In UKA v UKB [2018] SGHCF 7, I divided matrimonial assets equally between the parties in a 28-year marriage. I explained my decision involving this long Dual-Income marriage (at [82]):\n
                    82 This marriage was an equal partnership of different efforts and should be recognised as such in the division of assets. A just and equitable division of the matrimonial assets is for the parties to share equally in the wealth of this marriage. In reaching this decision, I am not painting a picture of a long and happy marriage where parties felt they were equals as marriage partners. Unfortunately, the evidence showed that the marital relationship had been strained and difficult for more than a decade before the divorce. I have found the Wife to be domineering and controlling. I doubt that the Husband felt as if he was an equal marriage partner, as the Wife controlled the finances so tightly that he struggled to find funds for himself. The Wife, on the other hand, has enjoyed the “high life”. But I have found that each played their roles, even if it was amidst quarrels and strained relationships. The parties married in their twenties, when neither had wealth nor high education. They journeyed together and at the end of their marriage, in their fifties, they had amassed more than $30 million in assets. Would they have acquired more or less assets had things been different? Suppose the Husband had limited the Wife from living the high life and spending so much money on the luxury goods? Suppose the Husband had spent less time on the Company and more time with the Wife? Suppose the parties had shared more equally the control over the Company’s finances? Who knows how things might have turned out? It is impossible to tell where each party would be today if some things had been different. My point is that parties should not now focus on the alleged misconduct of the other party, suggesting that he or she would have been in a better position had the other behaved better. Life is more complex than that.\n
                    \n
                    Sample output 3:\n
                    "Adjustments were for": The court was of the opinion that it was just and equitable to adjust the average ratio, which is the furthest range of what was acceptable as a proportion that inclines towards equality. \n
                    \n
                    Sample input 4: In the circumstances, the DJ was not wrong to award the Wife an uplift of 5%. Thus I awarded the Wife 50% of the pool of MAs.\n
                    \n
                    Sample output 4:\n
                    "Adjustments were for": Adverse inference drawn against husband for withdrawing large sums within a year of the IJ without reasonable explanation\n
                    \n
                    Sample input 5: In the case of Chan Yuen Boey v Sia Hee Soon [2012] 3 SLR 402. Steven Chong J (as he then was) observed at [34] that, from his review of the cases, the proportion awarded to homemaker wives who had made modest financial contribution to marriages lasting 17 to 35 years with children ranged between 35% to 50% of the total matrimonial assets. At [35] Chong J observed that the exceptions, where the apportionment in favour of the wife was less than 35%, typically involved cases where the total pool of matrimonial assets had been very substantial in excess of $100m. In those exceptional circumstances, the apportionment to the wife had nevertheless been substantial in absolute terms. Taking into account all factors in the round, and bearing in mind the value of the assets in the matrimonial pool, the fact that the Wife had made some direct financial contributions to the pool (albeit qualified by comments at [56] above), the Husband’s demonstrated proclivity to be less than open about his income and assets, and the concern not to double count, I held that it was just and equitable to award to the Wife 45% of the assets in the matrimonial pool, giving a ratio of 45:55 in favour of the Husband.\n
                    \n
                    Sample output 5:\n
                    "Adjustments were for": Husband had been less than open about his income and assets\n
                    \n
                    Sample input 6:  After considering all the circumstances of this case, I decided to award the Plaintiff a 42% share and the Defendant a 58% share of the entire pool of matrimonial assets. In my view, this would be a just and equitable division having regard to the extent of their relative financial and non-financial contributions from the date of marriage to the date of Interim Judgment.\n
                    \n
                    Sample output 6:\n
                    "Adjustments were for": Just and equitable having considered all the circumstances (at [33])\n
                    \n
                    Sample input 7:  An average of the two ratios is the next step. Referencing ANJ at [27] and Twiss at [21], the Court of Appeal has advised that adjustments could be made between the financial and non-financial ratios, having regard to the pool of assets and length of marriage. Here, the pool of assets is large, and the Father started acquiring the London properties prior to their marriage, which was a 10-year union. Greater weightage ought to be given to the direct contributions. Considering all the circumstances, I am of the view that awarding the Mother a 25% share of the total pool of matrimonial assets would be appropriate.\n
                    \n
                    Sample output 7:\n
                    "Adjustments were for": Greater weight given to direct contributions because of large pool of assets, 10-year marriage\n
                    \n
                    Sample input 8:  Given that the disparity between the ratio of direct financial contributions, 70:30, and the ratio of the indirect contributions, 75:25, was rather small, we thought that it would not be inapt simply to take the latter ratio as representative of the parties’ overall contributions to the matrimonial home. We therefore took the view that a fair and equitable division of the matrimonial home would be in the proportions of 75% to the wife and 25% to the husband.\n
                    \n
                    Sample output 8:\n
                    "Adjustments were for": CA adopted the indirect ratio as a fair and proportionate representation of parties' contributions to matrimonial home\n
                    \n
                    Sample input 9:  We therefore uphold the ratios assessed by the Judge, and her order for the equal division of the matrimonial assets between the parties.\n
                    \n
                    Sample output 9:\n
                    "Final ratio (post-adjustments)": 50\n
                    "Adjustments were for": We therefore uphold the ratios assessed by the Judge, and her order for the equal division of the matrimonial assets between the parties. (at [14])
                    \n
                    Judgment data:\n
                    {judgment_full_text}
                    """
            }
        ]
    )
    response_json = json.dumps(response.__dict__, default=lambda o: o.__dict__)
    with open("response.json", "w") as f:
        f.write(response_json)
    return response_json

def append_to_judgment(item, file_path):
    with open(file_path, 'r', encoding="utf-8") as file:
        json_data = json.load(file)
    json_data["gpt4_response"] = json.loads(item)
    with open(file_path, 'w', encoding="utf-8") as file:
        json.dump(json_data, file, indent=4, ensure_ascii=False)
    return (file_path + " updated.")

folder_path = "test_judgments/"

for file_name in os.listdir(folder_path):
    if file_name.endswith('.json'):
        startTime = time.time()
        print("Processing file:", file_name)
        
        json_file_path = os.path.join(folder_path, file_name)
        full_text = get_full_text_from_judgment(json_file_path)
        claude_response = claude3_api_call(full_text)
        append_to_judgment(claude_response.content[0].text, json_file_path)
        print("Completed file:", file_name)
        
        endTime = time.time()
        elapsedTime = endTime - startTime
        
        with open("logs.csv", "a", newline='') as file:
            writer = csv.writer(file)
            writer.writerow([file_name, elapsedTime, claude_response.usage.input_tokens + claude_response.usage.output_tokens])