#ifndef UINT256_H
#define UINT256_H

#include <stdint.h>

// Data type representing a 256-bit unsigned integer, represented
// as an array of 4 uint64_t values. It is expected that the value
// at index 0 is the least significant, and the value at index 3
// is the most significant.
//
// Don't make any changes to the representation of this data type.
// (I.e., don't add fields, remove fields, change names of fields, etc.)
typedef struct {
  uint64_t data[4];
} UInt256;

// Create a UInt256 value from a single uint64_t value.
// Only the least-significant 64 bits are initialized directly,
// all other bits are set to 0.
UInt256 uint256_create_from_u64(uint64_t val);

// Create a UInt256 value from an array of 4 uint64_t values.
// The element at index 0 is the least significant, and the element
// at index 3 is the most significant.
UInt256 uint256_create(const uint64_t data[4]);

// Create a UInt256 value from a string of hexadecimal digits.
UInt256 uint256_create_from_hex(const char *hex);

// Return a dynamically-allocated string of hex digits representing the
// given UInt256 value.
char *uint256_format_as_hex(UInt256 val);

// Get 64 bits of data from a UInt256 value.
// Index 0 is the least significant 64 bits, index 3 is the most
// significant 64 bits.
uint64_t uint256_get_bits(UInt256 val, unsigned index);

// Compute the sum of two UInt256 values.
UInt256 uint256_add(UInt256 left, UInt256 right);

// Compute the difference of two UInt256 values.
UInt256 uint256_sub(UInt256 left, UInt256 right);

// Compute the product of two UInt256 values.
UInt256 uint256_mul(UInt256 left, UInt256 right);

// You may add additional functions if you would like to

#endif // UINT256_H
