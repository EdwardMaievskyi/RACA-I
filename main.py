"""
Main application demonstrating the CodeAgent usage.
"""

from core.code_agent import CodeAgent, generate_code


def main():
    """Demonstrate CodeAgent usage."""
    
    # Example 1: Using the CodeAgent class
    agent = CodeAgent(verbose=True)
    
    # Generate and execute code
    user_request = ["Create a function that pulls BTC-USD ticker data for the last 30 days from the yahoo finance API and returns it as a prettified plain text table",
                    'Calculate the 10th prime number']
    result = agent.generate_and_execute(user_request[1])
    
    if result.success:
        print(f"Result: {result.output}")
        # Save the code to a file
        #agent.save_code(result, "prime_finder.py")
    
    print("\n" + "="*60 + "\n")
"""  
    # Example 2: Using the convenience function
    result2 = generate_code("Create a function that pulls BTC-USD ticker data for the last 30 days from the yahoo finance API and returns it as a prettified console table", execute=False)
    
    if result2.success:
        print("Generated code:")
        print(agent.get_full_code(result2))
"""


if __name__ == "__main__":
    main()
